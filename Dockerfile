from python:3.6

ENV HOME /home/litbot
RUN mkdir -p $HOME
WORKDIR $HOME

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY courses_data courses_data
COPY courses_db courses_db
COPY timetables timetables
COPY utils utils
COPY bot.py .
COPY res.py .

EXPOSE 8080

CMD ["python", "bot.py"]