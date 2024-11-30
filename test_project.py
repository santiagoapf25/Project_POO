import unittest
from flask import Flask, jsonify
import time
from project_poo import app, BotRPA, Mediciones, Ping, Graficador  # Asegúrate de que el nombre del archivo sea project2.py

class TestBotRPA(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.bot = BotRPA()

    def test_ping_success(self):
        # Realiza un ping a un host válido (por ejemplo, 8.8.8.8) y verifica que la latencia no sea None
        latency, error = Ping.realizar_ping("8.8.8.8")
        self.assertIsNotNone(latency)
        self.assertIsNone(error)

    def test_ping_failure(self):
        # Realiza un ping a un host inválido y verifica que no se obtenga latencia
        latency, error = Ping.realizar_ping("nonexistent.host")
        self.assertIsNone(latency)
        self.assertIsNone(error)

    def test_analizar_datos(self):
        # Test de la función de análisis de datos, donde incluimos un valor atípico
        data = [0.2, 0.3, 0.4, 0.5, 5.0]  # El 5.0 debe ser identificado como anomalía
        anomalies = self.bot.mediciones.analizar_datos(data)
        self.assertIn(5.0, anomalies)  # Verifica que 5.0 esté en las anomalías

    def test_graficar_latencias(self):
        # Test para graficar las latencias y asegurarse de que la imagen base64 no esté vacía
        self.bot.mediciones.latencias = [0.2, 0.3, 0.4, 0.5, 5.0]
        img = self.bot.graficador.graficar(self.bot.mediciones.latencias, "Test de Latencias", "Número de medición", "Latencia (s)", "Latencias", 'o', 'green')
        self.assertIsNotNone(img)
        self.assertTrue(len(img) > 100)  # La imagen debe tener contenido (base64)

    def test_generar_csv_data(self):
        # Verifica la generación de datos CSV correctamente
        self.bot.mediciones.latencias = [0.2, 0.3, 0.4, 0.5, 5.0]
        self.bot.mediciones.anomalies_latencias = [5.0]
        csv_data = self.bot.mediciones.generar_csv_data()
        self.assertEqual(len(csv_data), 5)
        self.assertEqual(csv_data[0]['Latencia (s)'], 0.2)
        self.assertEqual(csv_data[4]['Anomalía Latencia'], 'Sí')  # Verifica que la última latencia tenga "Sí" como anomalía


class TestFlaskApp(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = app.test_client()

    def test_index(self):
        """Prueba la ruta principal"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_iniciar_mediciones(self):
        """Prueba que la ruta /iniciar_mediciones funcione correctamente"""
        response = self.client.get('/iniciar_mediciones')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Mediciones iniciadas", response.data)

    def test_obtener_resultados(self):
        """Prueba que la ruta /obtener_resultados devuelva los resultados correctos"""
        # Agregamos el contexto de la aplicación para que funcione con Flask
        with app.app_context():
            self.client.get('/iniciar_mediciones')  # Llamamos primero a iniciar mediciones
            time.sleep(2)  # Esperamos a que el bot haya terminado las mediciones
            response = self.client.get('/obtener_resultados')
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertTrue(data["completadas"])
            self.assertIsNotNone(data["latencias_img"])
            self.assertIsInstance(data["csv_data"], list)


if __name__ == '__main__':
    unittest.main()
