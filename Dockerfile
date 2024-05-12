FROM python:3-alpine

WORKDIR /app

# Add tzdata and set default timezone
RUN apk add --no-cache tzdata
RUN ln -fs /usr/share/zoneinfo/Etc/UTC /etc/localtime

# Copy requirements and install them
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Run the application
CMD [ "python", "main.py" ]
