import time
from openai import AzureOpenAI
from azure_tennis_api.config import Config

# Initialize Azure OpenAI client
client = AzureOpenAI(
    azure_endpoint=Config.AZURE_OPENAI_ENDPOINT,
    api_key=Config.AZURE_OPENAI_KEY,
    api_version=Config.AZURE_OPENAI_VERSION
)

def clean_transcript_with_llm(transcript_text, video_title):
    """Clean and improve the transcript using Azure OpenAI"""
    try:
        #system prompt
        system_prompt = f"""
        You are an expert in cleaning and enhancing sports commentary transcripts, specifically tennis match broadcasts. Your task is to transform raw transcript text into clean, readable commentary while preserving all tennis-specific information that would be valuable for AI analysis.

        CLEANING TASKS:
        1. Fix grammar, punctuation, and capitalization
        2. Remove filler words ("um", "uh", "like", "you know", etc.)
        3. Fix sentence structure and organize into logical paragraphs
        4. Correct obvious speech-to-text errors while maintaining original meaning
        5. Format dialogue and commentary naturally

        CRITICAL PRESERVATION REQUIREMENTS:
        - Keep ALL player names, scores, and statistics EXACTLY as mentioned
        - Preserve ALL tactical observations and strategy discussions
        - Maintain ALL match momentum descriptions and turning points
        - Keep ALL technical tennis terminology (serves, volleys, approaches, etc.)
        - Preserve ALL emotional moments and crowd reactions
        - Maintain ALL time references and match progression details
        - Keep ALL coaching box interactions and player behavior observations
        - Preserve ALL tournament context and historical references

        TENNIS-SPECIFIC FORMATTING:
        - Organize commentary around natural breaks (games, sets, key points)
        - Group related tactical discussions together
        - Separate crowd/atmosphere observations into logical sections
        - Maintain chronological flow of match events
        - Preserve the relationship between cause and effect in commentary

        AVOID:
        - Adding information not in the original transcript
        - Changing any factual details, scores, or statistics
        - Removing any tennis analysis or strategic observations
        - Altering player behavior descriptions or emotional moments
        - Condensing important rally descriptions or key point analysis

        Video Title: {video_title}

        Return ONLY the cleaned transcript that maintains all tennis analysis value while being properly formatted and readable. Do not add explanations, introductions, or commentary about the cleaning process.
        """
        
        # Checks if transcript is too long
        max_length = 12000
        if len(transcript_text) > max_length:
            return chunk_and_process_transcript(transcript_text, video_title, system_prompt)
        
        # Calls Azure OpenAI API
        response = client.chat.completions.create(
            model=Config.AZURE_OPENAI_DEPLOYMENT,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": transcript_text}
            ],
            temperature=0.3,
            max_tokens=4000
        )
        
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        print(f"Error cleaning transcript: {str(e)}")
        return transcript_text

def chunk_and_process_transcript(transcript_text, video_title, system_prompt):
    """Process long transcripts by chunking them and processing each chunk separately"""
    #chunk size in characters
    chunk_size = 8000
    
    # Spliting transcript into chunks
    words = transcript_text.split()
    chunks = []
    current_chunk = []
    current_length = 0
    
    for word in words:
        word_len = len(word) + 1
        if current_length + word_len > chunk_size and current_chunk:
            chunks.append(' '.join(current_chunk))
            current_chunk = [word]
            current_length = word_len
        else:
            current_chunk.append(word)
            current_length += word_len
    
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    print(f"Transcript split into {len(chunks)} chunks for processing")
    
    # Process each chunk
    processed_chunks = []
    for i, chunk in enumerate(chunks):
        print(f"Processing chunk {i+1}/{len(chunks)}...")
        
        chunk_prompt = f"""
        This is part {i+1} of {len(chunks)} of a transcript. 
        {system_prompt}
        """
        
        try:
            if i > 0:
                time.sleep(1)
                
            response = client.chat.completions.create(
                model=Config.AZURE_OPENAI_DEPLOYMENT,
                messages=[
                    {"role": "system", "content": chunk_prompt},
                    {"role": "user", "content": chunk}
                ],
                temperature=0.3,
                max_tokens=4000
            )
            
            processed_chunks.append(response.choices[0].message.content.strip())
        
        except Exception as e:
            print(f"Error processing chunk {i+1}: {str(e)}")
            # Keep original chunk if processing fails
            processed_chunks.append(chunk)
    
    # Join processed chunks
    return '\n\n'.join(processed_chunks)