## setting


- ### .venv/lib/python3.8/site-packages/trp.pth -> trp경로 추가
    - trp_drf 폴더에서 trp 폴더 import 가능
- ### /etc/apache2/apache2.conf에 아래 내용 추가

        WSGIApplicationGroup %{GLOBAL}
        
    - Truncated or oversized response headers received from daemon process 'trp-api': /home/kingbus/trp/trp_drf/trp_drf/wsgi.py 에러 해결