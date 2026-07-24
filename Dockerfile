FROM mosecorg/mosec:0.9.7

WORKDIR /app

COPY server.py /app/server.py

EXPOSE 8000

CMD ["python", "server.py"]