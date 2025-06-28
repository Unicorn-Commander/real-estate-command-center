FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y     python3 python3-pip python3-pyqt5 qt5-default xvfb     libgl1-mesa-glx libegl1 libglib2.0-0 libxkbcommon-x11-0 libxcb-xinerama0 x11-apps
WORKDIR /app
COPY desktop /app/desktop
COPY desktop/requirements.txt ./requirements.txt
RUN pip3 install --upgrade pip && pip3 install -r requirements.txt
ENV DISPLAY=:99
CMD ["/bin/bash"]
