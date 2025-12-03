from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from groq import Client

# Obtener la clave desde las env vars de Render
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = Client(api_key=GROQ_API_KEY)


app = FastAPI()

# CORS para frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Para desarrollo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Conversaciones por usuario
conversations = {}

# Mensaje inicial de sistema para rol de soporte
SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "Eres un asistente virtual de soporte técnico de la empresa llamada AC21. "
        "Tu trabajo es ayudar a los usuarios de forma clara, amable y profesional. "
        "Responde a todas las preguntas relacionadas con los productos, "
        "la plataforma y cualquier duda técnica de manera precisa y cordial."
        "No te desvies del tema y mantén siempre un tono profesional."
"Si te preguntan algo muy especifico (precios,etc...) , indica que en la parte inferior derecha de la página puede ponerse en contacto con un humano"
        "En caso de decir precios no digas cifras exactas, solo menciona que pueden contactar con un humano para más detalles."
        "Si te preguntan algo que no tiene nada que ver con el ámbito di: No te puedo ayudar con eso."
    )
}

# Productos y respuestas automáticas
PRODUCT_RESPONSES = {
    "GNSS": "Hola, veo que tienes dudas sobre GNSS. ¿Qué necesitas saber específicamente?",
    "DRONE": "Estás preguntando sobre DRONES. ¿Quieres información técnica, soporte o una oferta?",
    "LIDAR": "Sobre LIDAR, puedo darte detalles técnicos o precios. ¿Qué prefieres?",
    "SLAM": "SLAM es un sistema avanzado de mapeo. ¿Qué consulta tienes?",
    "USV": "Los USV son sistemas de vehículos autónomos. ¿Qué información necesitas?",
    "AGRICULTURA": "En agricultura, tenemos sensores y drones especializados. ¿Qué te interesa?"
}

class ChatRequest(BaseModel):
    user_id: str
    message: str

@app.post("/chat")
def chat_endpoint(request: ChatRequest):
    user_id = request.user_id
    user_message = request.message.strip()

    # Inicializar conversación con mensaje de sistema si es la primera vez
    if user_id not in conversations:
        conversations[user_id] = [SYSTEM_PROMPT]

    # Agregar mensaje del usuario
    conversations[user_id].append({"role": "user", "content": user_message})

    # Revisar si menciona un producto conocido
    product_found = None
    for product in PRODUCT_RESPONSES.keys():
        if product.lower() in user_message.lower():
            product_found = product
            break

    if product_found:
        bot_message = PRODUCT_RESPONSES[product_found]
        conversations[user_id].append({"role": "assistant", "content": bot_message})
    else:
        # Usar Groq Llama 3.1 para respuesta general
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=conversations[user_id]
        )
        bot_message = response.choices[0].message.content

        conversations[user_id].append({"role": "assistant", "content": bot_message})

    return {"response": bot_message}
