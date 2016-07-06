FROM python:2-onbuild
CMD ["gunicorn", "app", "-b", "0.0.0.0:8000", "--log-file", "-"]
