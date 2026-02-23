# 1. Use an official lightweight Python image
FROM python:3.9-slim

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Copy your requirements file and install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# 4. Copy the rest of your app's code into the container
COPY . .

# 5. The startup command your lab encouraged you to use!
CMD ["streamlit", "run", "gotham_ai_report.py", "--server.port=8080", "--server.address=0.0.0.0"]