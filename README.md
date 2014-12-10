Blohaute
========

BloHaute Website

##Installation

1. Create an environment outside the repo using virtualenv to hold your packages
````
virtualenv PROJECT_NAME --no-site-packages
```

2. Activate the environment
```
source PROJECT_NAME/bin/activate
```

3. Install django
```
pip install django
```

4. Change to the project directory and run
```
python manage.py migrate
python manage.py runserver
```

5. Open your browser to the page given
