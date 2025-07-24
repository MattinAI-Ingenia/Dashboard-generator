import streamlit as st
import requests
import json
import matplotlib.pyplot as plt
st.title("Consulta a base de datos")
query = st.text_input("Escribe tu consulta en lenguaje natural")

if st.button("Enviar"):
    url ="http://langflow:7860/api/v1/run/0445bac0-e9e8-462f-b3f0-cd1c0eba0826"
    
    payload = {
        "input_value": query,
        "output_type": "text",
        "input_type": "text"
    }
    headers = {
        "Content-Type": "application/json"
    }

    try:
        
        response = requests.request("POST", url, json=payload, headers=headers)
        response.raise_for_status()
        # response_dict = json.loads(response.text)
        # st.write(response_dict)
        if response.ok:
            # st.success(response.json())
            response_dict = json.loads(response.text)
            data = response_dict['outputs'][0]['outputs'][0]['results']['text']['data']['text']
            clean_json_str = data.strip('```json').strip('```').strip()

            # Parsear el JSON como dict
            parsed_result = json.loads(clean_json_str)
            count = parsed_result["result"][0]["count"]

            
        else:
            st.error('Error')
        
    # Mostrar la gráfica
        st.title("Conteo de Modelos en la Base de Datos")

        fig, ax = plt.subplots()
        ax.bar(["Modelos"], [count], color='skyblue')
        ax.set_ylabel("y")
        ax.set_title("Gráfica generada")

        st.pyplot(fig)
    
    except requests.exceptions.RequestException as e:
        print(f"Error making api resqiest: {e}")
    except ValueError as e:
        print(f"Error parsing response: {e}")

        