from openai import AzureOpenAI
from config import Config

#Azure OpenAI client
client = AzureOpenAI(
    azure_endpoint=Config.AZURE_OPENAI_ENDPOINT,
    api_key=Config.AZURE_OPENAI_KEY,
    api_version=Config.AZURE_OPENAI_VERSION
)

def chat_with_context(user_query, context, chat_history=None):
    """Generating a response based on transcript context"""
    if chat_history is None:
        chat_history = []
        
    try:
        system_prompt = f"""
        You are an AI assistant that helps answer questions about tennis matches based on video transcripts.
        Use only the provided context to answer the user's question. If the answer is not in the
        context, politely say that you don't have that information.
        
        Provide detailed and informative responses about tennis matches, players, scores, and statistics
        mentioned in the transcript. Respond in a conversational, helpful manner.

        Context:
        {context}
        """
        
        messages = [{"role": "system", "content": system_prompt}]
        
        # chat history
        for message in chat_history:
            messages.append({
                "role": message["role"],
                "content": message["content"]
            })
            
        # Adds the current query
        messages.append({"role": "user", "content": user_query})
        
        # Call Azure OpenAI API
        response = client.chat.completions.create(
            model=Config.AZURE_OPENAI_DEPLOYMENT,
            messages=messages,
            temperature=0.7,
            max_tokens=1000
        )
        
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        print(f"Error in chat completion: {str(e)}")
        return "I'm sorry, I encountered an error while processing your request."