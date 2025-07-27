#!/bin/bash

case "$OSTYPE" in
    msys*)    python=python ;;
    cygwin*)  python=python ;;
    *)        python=python3 ;;
esac

PATH_TO_MANAGE_PY=$(find ../ -name "manage.py" -not -path "*/env" -not -path "*/venv");
BASE_DIR="$(dirname "${PATH_TO_MANAGE_PY}")";
cd $BASE_DIR
status=$?;
if [ $status -ne 0 ]; then
    echo "Убедитесь, что в проекте содержится только один файл manage.py";
    exit $status;
fi

echo "from django.contrib.auth import get_user_model; User = get_user_model(); \
     usernames_list = ['+79123456789', '+79176665544', '+79123211232']; \
     delete_num, _ = User.objects.filter(phone_number__in=usernames_list).delete(); \
     exit(1) if not delete_num else exit(0);" | $python manage.py shell
status=$?;
if [ $status -ne 0 ]; then
    echo "Ошибка при удалении записей, созданных в БД на предыдущем запуске postman-коллекции: объекты отсутствуют либо произошел сбой.";
    exit $status;
fi
echo "База данных очищена."