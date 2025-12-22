# app/workers/health_worker.py
from faststream import FastStream
from faststream.rabbit import RabbitBroker

broker = RabbitBroker("amqp://guest:guest@localhost:5672/")
app = FastStream(broker)

@broker.subscriber("health.ping")
async def health_ping():
    return {"status": "pong", "service": "health_worker"}

@app.after_startup
async def on_startup():
    await broker.publish({"status": "started"}, "health.status")