from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, udf
from pyspark.sql.types import StringType, StructType, StructField, ArrayType
import json
import base64
from transformers import AutoTokenizer

from chunker import semantic_chunk
from cleaner import clean_text
import uuid

# Initialize Spark Session
spark = SparkSession.builder \
    .appName("DocumentProcessingPipeline") \
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1") \
    .getOrCreate()

# Load Tokenizer once per worker
tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")

# Define schema for incoming Kafka messages
raw_doc_schema = StructType([
    StructField("doc_id", StringType(), True),
    StructField("source", StringType(), True),
    StructField("content_type", StringType(), True),
    StructField("raw_content", StringType(), True),
    StructField("metadata", StringType(), True),  # Stringified JSON
    StructField("ingested_at", StringType(), True)
])

def process_document(doc_id, raw_content_b64, metadata_str):
    try:
        # Decode content
        raw_content = base64.b64decode(raw_content_b64).decode('utf-8')
        
        # Clean
        cleaned = clean_text(raw_content)
        
        # Chunk
        chunks = semantic_chunk(cleaned, tokenizer)
        
        # Format as ProcessedChunk JSON strings
        metadata = json.loads(metadata_str) if metadata_str else {}
        processed_chunks = []
        for i, text in enumerate(chunks):
            chunk_data = {
                "chunk_id": str(uuid.uuid4()),
                "doc_id": doc_id,
                "text": text,
                "chunk_index": i,
                "token_count": len(tokenizer.encode(text)),
                "metadata": metadata
            }
            processed_chunks.append(json.dumps(chunk_data))
        return processed_chunks
    except Exception as e:
        return []

process_udf = udf(process_document, ArrayType(StringType()))

# Read from Kafka
df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:9092") \
    .option("subscribe", "raw-documents") \
    .option("startingOffsets", "earliest") \
    .load()

# Parse JSON values
parsed_df = df.select(
    from_json(col("value").cast("string"), raw_doc_schema).alias("data")
).select("data.*")

# Process the documents (cleaning + chunking)
processed_df = parsed_df.withColumn(
    "chunks", 
    process_udf(col("doc_id"), col("raw_content"), col("metadata"))
)

# Explode the array of chunks into individual rows
from pyspark.sql.functions import explode
exploded_df = processed_df.select(explode(col("chunks")).alias("value"))

# Write to Kafka
query = exploded_df.writeStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:9092") \
    .option("topic", "processed-chunks") \
    .option("checkpointLocation", "/tmp/spark-checkpoints") \
    .start()

query.awaitTermination()
