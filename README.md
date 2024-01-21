# About project

  This is my project where I implemented functionality for user interaction with the server and other users using the WebSocket protocol.   I integrated the WebSocket protocol into Django using Channels and utilized Redis as the channel layer. I retrieved real-time cryptocurrency price data through a Celery background task and WebSocket connection to the CoinCapApi. In this project, I aimed to make use of everything Django offers, from view functions to signals and changing the communication interface with the web server. On the frontend, HTML with DTL (Django Template Language)/Bootstrap/JavaScript is used, and Plotly is employed for building and updating price charts. For storing the data I use PostgreSQL.
  
# How to set up this project
  1. Copy the repository - git clone https://github.com/WindowJump/django-trade
  2. Build the project using Docker-compose - docker-compose build
  3. Up the project - docker-compose up
  4. Make migration - docker-compose run --rm web-app sh -c "python manage.py migrate"
  5. Setup the database - 1) docker-compose run --rm web-app sh -c "python manage.py shell"
                          2) from app_dir.supported_coins import db_init
                          3) db_init()
       This will create needed records in db and create 2 active users (username=user1, user2; password='4vH6v^Z,2c_') with some BTC/USDT balance so you can make       
     offers/transactions on the site.
# Contact Me
If you saw any mistakes/problems please, feel free to contact with me andriybalabushka@ukr.net or telegram @xddinside
