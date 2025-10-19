import google.generativeai as genai
import PIL.Image
import os
import json
import chromadb
from dotenv import load_dotenv
import uuid
from datetime import datetime

load_dotenv()

api_key = os.getenv("API_KEY")
chromadb_key = os.getenv("CHROMA_API_KEY")
tenant_key = os.getenv("CHROMA_TENANT")
database_name = os.getenv("CHROMA_DATABASE")

def extract_prescription_data_gemini(image_path, api_key):
    """
    Extract prescription data using Google Gemini Vision API
    """
    genai.configure(api_key=api_key)
    
    # Load the image
    img = PIL.Image.open(image_path)
    
    # Initialize the model
    model = genai.GenerativeModel('gemini-2.5-flash-lite')
    
    prompt = """Extract all the data from this medical prescription and return it as structured text.
    For each piece of information, create a separate line with clear labels:
    
    DOCTOR_NAME: [doctor's name]
    DOCTOR_QUALIFICATION: [qualifications]
    DOCTOR_REGISTRATION: [registration number]
    PATIENT_NAME: [patient's name]
    PATIENT_AGE: [age]
    PATIENT_GENDER: [gender]
    PRESCRIPTION_DATE: [date]
    DIAGNOSIS: [diagnosis/condition]
    
    For each medication, use this format:
    MEDICATION: [name] | DOSAGE: [dosage] | FREQUENCY: [how often] | DURATION: [how long] | INSTRUCTIONS: [special instructions]
    
    ADDITIONAL_NOTES: [any other notes]
    
    Extract all visible information. If something is not visible, skip that line."""
    
    response = model.generate_content([prompt, img])
    
    return response.text

def initialize_chromadb():
    """
    Initialize ChromaDB client and get or create collection
    """
    client = chromadb.CloudClient(
        api_key=chromadb_key,
        tenant=tenant_key,
        database=database_name
    )
    
    # Get or create collection for medical prescriptions
    try:
        collection = client.get_collection(name="medical_prescriptions")
    except:
        collection = client.create_collection(name="medical_prescriptions")
    
    return collection

def store_prescription_in_vectordb(extracted_text, image_path, collection):
    """
    Store prescription data in ChromaDB - each piece of information as separate document for better RAG
    """
    try:
        # Parse the structured text into individual components
        lines = extracted_text.strip().split('\n')
        
        # Base prescription ID for grouping related documents
        base_prescription_id = str(uuid.uuid4())[:8]
        
        # Storage containers
        documents = []
        metadatas = []
        ids = []
        
        # Base metadata for all documents
        base_metadata = {
            "source_image": image_path,
            "extraction_date": datetime.now().isoformat(),
            "prescription_id": base_prescription_id
        }
        
        # Track extracted information for summary
        prescription_info = {}
        
        # Process each line
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if ':' in line:
                key_value = line.split(':', 1)
                if len(key_value) == 2:
                    key = key_value[0].strip()
                    value = key_value[1].strip()
                    
                    if value and value.lower() != 'n/a':
                        # Store individual information pieces
                        if key in ['DOCTOR_NAME', 'DOCTOR_QUALIFICATION', 'DOCTOR_REGISTRATION']:
                            doc_text = f"Doctor Information - {key.replace('_', ' ').title()}: {value}"
                            doc_type = "doctor_info"
                            prescription_info['doctor_name'] = prescription_info.get('doctor_name', '') + f" {value}"
                            
                        elif key in ['PATIENT_NAME', 'PATIENT_AGE', 'PATIENT_GENDER']:
                            doc_text = f"Patient Information - {key.replace('_', ' ').title()}: {value}"
                            doc_type = "patient_info"
                            if key == 'PATIENT_NAME':
                                prescription_info['patient_name'] = value
                            
                        elif key == 'PRESCRIPTION_DATE':
                            doc_text = f"Prescription Date: {value}"
                            doc_type = "prescription_details"
                            prescription_info['prescription_date'] = value
                            
                        elif key == 'DIAGNOSIS':
                            doc_text = f"Medical Diagnosis: {value}"
                            doc_type = "diagnosis"
                            prescription_info['diagnosis'] = value
                            
                        elif key == 'ADDITIONAL_NOTES':
                            doc_text = f"Additional Notes: {value}"
                            doc_type = "notes"
                            
                        else:
                            doc_text = f"{key.replace('_', ' ').title()}: {value}"
                            doc_type = "general_info"
                        
                        # Add to storage
                        documents.append(doc_text)
                        metadata = base_metadata.copy()
                        metadata["document_type"] = doc_type
                        metadata["info_key"] = key.lower()
                        metadatas.append(metadata)
                        ids.append(f"{base_prescription_id}_{key.lower()}_{len(ids)}")
            
            # Handle medication lines (format: MEDICATION: name | DOSAGE: dose | etc.)
            elif 'MEDICATION:' in line:
                # Parse medication line
                parts = line.split('|')
                med_info = {}
                
                for part in parts:
                    part = part.strip()
                    if ':' in part:
                        k, v = part.split(':', 1)
                        med_info[k.strip()] = v.strip()
                
                # Create comprehensive medication document
                med_name = med_info.get('MEDICATION', 'Unknown Medication')
                med_doc = f"Medication: {med_name}"
                
                if 'DOSAGE' in med_info:
                    med_doc += f" - Dosage: {med_info['DOSAGE']}"
                if 'FREQUENCY' in med_info:
                    med_doc += f" - Frequency: {med_info['FREQUENCY']}"
                if 'DURATION' in med_info:
                    med_doc += f" - Duration: {med_info['DURATION']}"
                if 'INSTRUCTIONS' in med_info:
                    med_doc += f" - Instructions: {med_info['INSTRUCTIONS']}"
                
                documents.append(med_doc)
                metadata = base_metadata.copy()
                metadata["document_type"] = "medication"
                metadata["medication_name"] = med_name
                if 'DOSAGE' in med_info:
                    metadata["dosage"] = med_info['DOSAGE']
                metadatas.append(metadata)
                ids.append(f"{base_prescription_id}_med_{len(ids)}")
        
        # Add a summary document
        summary_doc = f"Prescription Summary - "
        if 'doctor_name' in prescription_info:
            summary_doc += f"Doctor: {prescription_info['doctor_name'].strip()}, "
        if 'patient_name' in prescription_info:
            summary_doc += f"Patient: {prescription_info['patient_name']}, "
        if 'prescription_date' in prescription_info:
            summary_doc += f"Date: {prescription_info['prescription_date']}, "
        if 'diagnosis' in prescription_info:
            summary_doc += f"Diagnosis: {prescription_info['diagnosis']}"
        
        documents.append(summary_doc)
        summary_metadata = base_metadata.copy()
        summary_metadata["document_type"] = "summary"
        summary_metadata.update(prescription_info)
        metadatas.append(summary_metadata)
        ids.append(f"{base_prescription_id}_summary")
        
        # Batch add to ChromaDB
        if documents:
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            print(f"✅ Successfully stored {len(documents)} documents in ChromaDB")
            print(f"📋 Prescription ID: {base_prescription_id}")
            print(f"📄 Documents created:")
            for i, doc in enumerate(documents):
                print(f"   {i+1}. {doc[:80]}{'...' if len(doc) > 80 else ''}")
            
            return base_prescription_id
        else:
            print("❌ No valid data found to store")
            return None
        
    except Exception as e:
        print(f"❌ Error storing in ChromaDB: {e}")
        print("Raw response:", extracted_text)
        return None

# Usage

def process_prescription_with_vectorization(image_path):
    """
    Complete pipeline: OCR extraction + ChromaDB storage
    """
    print(f"🔍 Processing image: {image_path}")
    
    # Extract prescription data using Gemini
    print("📄 Extracting prescription data...")
    extracted_text = extract_prescription_data_gemini(image_path, api_key)
    print("✅ Extraction complete!")
    print("📋 Extracted Data:")
    print(extracted_text)
    
    # Initialize ChromaDB
    print("\n🔗 Connecting to ChromaDB...")
    collection = initialize_chromadb()
    
    # Store in vector database
    print("💾 Storing in vector database...")
    prescription_id = store_prescription_in_vectordb(extracted_text, image_path, collection)
    
    if prescription_id:
        print(f"\n🎉 Successfully processed and stored prescription!")
        print(f"📊 Collection stats: {collection.count()} total prescriptions")
    
    return extracted_text, prescription_id

# Main execution
if __name__ == "__main__":
    image_path = "Medical-Report-1-Ibadan.jpg"
    
    # Process prescription with full pipeline
    result, doc_id = process_prescription_with_vectorization(image_path)
    
    # Optional: Query example (for testing RAG setup)
    print("\n" + "="*50)
    print("🔍 Testing RAG query capability...")
    collection = initialize_chromadb()
    
    # Example queries to test different types of information retrieval
    test_queries = [
        "patient information and details",
        "prescribed medications and dosages", 
        "doctor information",
        "medical diagnosis"
    ]
    
    for query in test_queries:
        print(f"\n🔎 Query: '{query}'")
        query_results = collection.query(
            query_texts=[query],
            n_results=3
        )
        
        if query_results['documents']:
            print("📋 Found relevant information:")
            for i, doc in enumerate(query_results['documents'][0]):
                metadata = query_results['metadatas'][0][i]
                print(f"  {i+1}. [{metadata.get('document_type', 'unknown')}] {doc}")
        else:
            print("   No results found")
        print("-" * 40)