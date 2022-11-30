FROM openeuler/openeuler:20.03-lts-sp3
COPY ./oecpreport /app
COPY ./oecp-report /app
COPY ./requirements.txt /app
WORKDIR /app
RUN mkdir -p /etc/oecpreport
RUN mkdir -p /var/log/oecp
COPY ./conf.ini /etc/oecpreport
RUN yum install git libabigail python3-uWSGI python3-pip createrepo -y
RUN git clone https://gitee.com/openeuler/oecp.git /app/oecp
RUN chmod +x oecp-report
RUN chmod -R 777 /app
RUN pip3 install -i https://pypi.douban.com/simple/ -r requirements.txt 
RUN pip3 install -i https://pypi.douban.com/simple/ -r /app/oecp/requirement
EXPOSE 5000
ENV LANG C.UTF-8
ENV SETTINGS_FILE /etc/oecpreport/conf.ini
CMD ["/bin/bash","oecp-report","run"]
