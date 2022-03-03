FROM python:3
WORKDIR /mydata
ADD . /mydata
RUN pip install --no-cache-dir -r requirements.txt
CMD ["python","parser.py"]