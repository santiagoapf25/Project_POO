import matplotlib
matplotlib.use('Agg')  # Establecer el backend 'Agg' para evitar errores

import time
import subprocess
import matplotlib.pyplot as plt
import base64
from io import BytesIO
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from flask import Flask, render_template, jsonify


app = Flask(__name__)

class Ping:
    @staticmethod
    def realizar_ping(host):
        try:
            start_time = time.time()
            subprocess.run(['ping', '-n', '1', host], capture_output=True, text=True, check=True)
            latency = time.time() - start_time
            return latency, None  # Retornar solo la latencia
        except subprocess.CalledProcessError as e:
            print(f"Error en el ping a {host}: {e}")
            return None, None
        


class Mediciones:
    def __init__(self):
        self.latencias = []
        self.anomalies_latencias = []
        self.mediciones_completadas = False

    def ejecutar_mediciones(self, host, num_mediciones):
        self.latencias = []
        for _ in range(num_mediciones):
            latency, _ = Ping.realizar_ping(host)
            if latency is not None:
                self.latencias.append(latency)
            time.sleep(0.5)

        self.anomalies_latencias = self.analizar_datos(self.latencias)
        self.mediciones_completadas = True

    def analizar_datos(self, data):
        if len(data) < 2:
            return []
        model = IsolationForest(contamination=0.1)
        preds = model.fit_predict(np.array(data).reshape(-1, 1))
        return [d for i, d in enumerate(data) if preds[i] == -1]

    def calcular_ancho_banda(self):
        if not self.latencias:
            return []
        return [1 / lat if lat > 0 else None for lat in self.latencias]

    def generar_csv_data(self):
        max_len = len(self.latencias)
        latencias = self.latencias
        ancho_banda = self.calcular_ancho_banda()
        df = pd.DataFrame({
            "Medición": list(range(1, max_len + 1)),
            "Latencia (s)": latencias,
            "Ancho de Banda (bps)": ancho_banda,
            "Anomalía Latencia": ["Sí" if lat in self.anomalies_latencias else "No" for lat in latencias],
        })
        return df.to_dict(orient="records")


class Graficador:
    @staticmethod
    def graficar(datos, titulo, xlabel, ylabel, label, marker, color):
        if not datos:
            return None

        plt.figure(figsize=(12, 5))
        x_values = range(1, len(datos) + 1)
        plt.xticks(range(1, len(datos) + 1))
        plt.plot(x_values, datos, label=label, marker=marker, color=color)

        plt.title(titulo)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.legend()
        plt.grid()

        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        plt.close()
        buffer.seek(0)
        return base64.b64encode(buffer.getvalue()).decode('utf-8')


class BotRPA:
    def __init__(self):
        self.mediciones = Mediciones()
        self.graficador = Graficador()

    def ejecutar_mediciones(self, host, num_mediciones):
        self.mediciones.ejecutar_mediciones(host, num_mediciones)

    def obtener_resultados(self):
        if self.mediciones.mediciones_completadas:
            latencias_img = self.graficador.graficar(
                self.mediciones.latencias,
                "Medición de Latencias",
                "Número de Medición",
                "Tiempo (s)",
                "Latencias",
                'o',
                'green'  # Color verde para las latencias
            )
            ancho_banda_img = self.graficador.graficar(
                self.mediciones.calcular_ancho_banda(),
                "Medición de Ancho de Banda",
                "Número de Medición",
                "Ancho de Banda (bps)",
                "Ancho de Banda",
                'x',
                'orange'  # Color naranja para el ancho de banda
            )
            csv_data = self.mediciones.generar_csv_data()
            return jsonify({
                "completadas": True,
                "latencias_img": latencias_img,
                "ancho_banda_img": ancho_banda_img,
                "csv_data": csv_data
            })
        return jsonify({"completadas": False})


bot = BotRPA()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/iniciar_mediciones')
def iniciar_mediciones():
    bot.ejecutar_mediciones('8.8.8.8', 15)  # Cambia el host y el número de mediciones según lo necesario
    return jsonify({"status": "Mediciones iniciadas"})


@app.route('/obtener_resultados')
def obtener_resultados():
    return bot.obtener_resultados()


if __name__ == '__main__':
    app.run(debug=True)