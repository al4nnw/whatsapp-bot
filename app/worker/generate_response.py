import asyncio
import json
import openai
import base64

from pydantic import ValidationError
from app.contracts.chat_session import ChatSession
from app.contracts.media import Media
from app.contracts.transactions import Transaction
from app.utils.system_prompt import SYS_PROMPT
from app.worker.exceptions import MissingContext, OutOfSubject
from app.worker.services.generate_user_prompt import generate_user_prompt

client = openai.Client()

async def generate_response(session: ChatSession) -> str:
    print(f"[generate_response] Processing {len(session.queue_user_messages)} messages from {session.user_id}...")
    
    compiled_prompt = await generate_user_prompt(session)
    
    try:
        bot_response = await asyncio.to_thread(send_to_openai, compiled_prompt)
        session.joined_user_messages.append(compiled_prompt)
        session.clean_user_messages()
    except MissingContext as mc:
        print(f"MissingContext exception: {mc}")
        bot_response = str(mc)
    except OutOfSubject as oos:
        session.clean_user_messages()
        print(f"OutOfSubject exception: {oos}")
        bot_response = str(oos)
    except Exception as e:
        session.clean_user_messages()
        print(f"Error during sending to OpenAI: {e}")
        return "Desculpe, ocorreu um erro inesperado. Por favor, tente novamente."
    
    print("[generate_response] Exiting generate_response with response:", bot_response)
    return bot_response
  


def send_to_openai(prompt: str) -> str:
    print("Entering send_to_openai with prompt:", prompt)
    print(f"[send_to_openai] Sending prompt to OpenAI: {prompt}")
    
    user_messages = get_user_messages(prompt)
    print("User messages generated:", user_messages)
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": SYS_PROMPT,
                    }
                ]
            },
            user_messages
        ],
        functions=[
            {
                "name": "extract_transaction",
                "description": "Extrai uma ou mais transações a partir do prompt do usuário",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "transactions": {
                            "type": "array",
                            "items": Transaction.model_json_schema(),
                            "description": "Uma lista de transações extraídas"
                        }
                    },
                    "required": ["transactions"]
                }
            },
            {
                "name": "user_out_of_subject",
                "description": "Usuário fora do assunto, utilize esta função toda vez que o usuário fugir do assunto.",
                "parameters": {}
            }
        ],
        function_call="auto",
        temperature=0.2,
        max_completion_tokens=2048,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    print("Received response from OpenAI:", response)
    
    message = response.choices[0].message
    function_call = message.function_call
    if not function_call:
        clarification = message.content or "Nenhuma resposta recebida."
        print("Function call missing, clarification needed:", clarification)
        raise MissingContext(f"Esclarecimento necessário: {clarification}")
    
    function_name = function_call.name or ""
    
    if function_name == "extract_transaction":
        transactions = extract_transactions(function_call)
        print("Extracted transactions:", transactions)
        response_message = "Transações extraídas com sucesso:\n"
        for txn in transactions:
            response_message += f"- {txn.title} ({txn.type}): R${txn.amount}\n"
        return response_message
    elif function_name == "user_out_of_subject":
        print("User out of subject detected.")
        raise OutOfSubject("O FinBot fala somente sobre finanças, por favor, mantenha-se no assunto.")
    else:
        print("Unknown function call detected:", function_name)
        raise MissingContext("Poderia me dar mais detalhes?")


def extract_transactions(function_call) -> list[Transaction]:
    print("Entering extract_transactions with function_call:", function_call)
    try:
        arguments_str = function_call.arguments or "{}"
        arguments = json.loads(arguments_str)
        print("Decoded arguments:", arguments)
    except json.JSONDecodeError as e:
        print("JSONDecodeError:", e)
        raise MissingContext("Erro ao extrair as informações, seja mais claro.")
    
    # Get transactions from the 'transactions' property
    transactions_data = arguments.get("transactions", [])
    
    if not isinstance(transactions_data, list):
        raise MissingContext("Formato inválido para a lista de transações.")
    
    if not transactions_data:
        raise MissingContext("Nenhuma transação encontrada na resposta.")
    
    transactions = []
    for idx, txn_data in enumerate(transactions_data):
        txn = validate_transaction_data(txn_data, index=idx)
        transactions.append(txn)
    
    print("Exiting extract_transactions with transactions:", transactions)
    return transactions


def validate_transaction_data(txn_data: dict, index: int = None) -> Transaction:
    """
    Valida os dados de uma transação e, em caso de erro, utiliza a exceção MissingContext
    para indicar qual campo está ausente ou com formato incorreto.
    """
    try:
        transaction = Transaction(**txn_data)
        print(f"Transação {index if index is not None else ''} validada com sucesso:", transaction)
        return transaction
    except ValidationError as ve:
        prefix = f"na transação {index} - " if index is not None else ""
        for error in ve.errors():
            loc = error.get("loc", ["unknown"])[0]
            error_msg = error.get("msg", "")
            if "field required" in error_msg:
                clarification_question = ask_missing_field(loc)
                print(f"Campo ausente detectado {prefix}'{loc}'")
                raise MissingContext(f"{prefix}Campo ausente '{loc}': {clarification_question}")
            else:
                clarification_question = handle_invalid_format(loc, str(txn_data.get(loc)))
                print(f"Formato inválido detectado {prefix}para o campo '{loc}'")
                raise MissingContext(f"{prefix}Formato inválido para o campo '{loc}': {clarification_question}")


def get_user_messages(prompt: str) -> list[dict]:
    print("Entering get_user_messages with prompt:", prompt)
    items = prompt.split("\n")
  
    messages = []
  
    for elem in items:
        if "###IMAGE_DOWNLOADED###" in elem:      
            path = elem.replace("###IMAGE_DOWNLOADED###", "")
            with open(path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            messages.append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                }
            )
        else:
            messages.append(
                {
                    "type": "text",
                    "text": elem,
                }
            )
  
    user_message = {
        "role": "user",
        "content": messages
    }
    print("Exiting get_user_messages with user_message:", user_message)
    return user_message



def ask_missing_field(field: str) -> str:
    print("Entering ask_missing_field for field:", field)
    question = f"Por favor, informe o valor para o campo obrigatório '{field}'."
    return question


def handle_invalid_format(field: str, value: str) -> str:
    print("Entering handle_invalid_format for field:", field, "with value:", value)
    response = (f"O valor fornecido para o campo '{field}' ('{value}') não está no formato correto. "
                "Por favor, informe o valor no formato adequado.")
    return response

