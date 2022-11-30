#!/bin/bash

function build_env(){
    docker-compose -v
    if [ $? -ne 0 ];then
        sudo curl -L https://github.com/docker/compose/releases/download/1.21.2/docker-compose-$(uname -s)-$(uname -m) -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
    fi
    docker-compose build
    docker-compose up
}

function run(){
    uwsgi -d --ini oecp.ini
    celery -A application.core.task.tasks:celery worker
}

case $1 in
start)
    build_env
    ;;
run)
    run
    ;;
*)
    echo 'unknown comand,try again run or start'
    ;;
esac
