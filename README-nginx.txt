RUNNING THIS PROJECT WITH NGINX LOCALLY
=======================================

To start the thread, just type this in::

 $ ./run_djangopeople_fcgi.sh
 
That will start a fcgi thread on port 9000. Review fcgi_settings.py to
see that it works for you.

To kill the fcgi thread delete the PID file::

 $ rm /tmp/djangopeoplenet.pid

Edit /etc/hosts so that kungfupeople.local points to 127.0.0.1. E.g.::

 127.0.0.1       localhost kungfupeople.local
 
Start nginx and put this into /etc/nginx/sites-enabled/djangopeople::



upstream djangoserv4 {
         server 127.0.0.1:9000;
}

server {
       listen 80;
       root /home/peterbe/djangopeoplenet;
       
       # $server_addr because Nagios connects via IP
       server_name kungfupeople.local;
       
       access_log /var/log/nginx/djangopeople.access.log;
       error_log /var/log/nginx/djangopeople.error.log;
       
       client_max_body_size 2M;
       
       gzip            on;
       gzip_http_version 1.0;
       gzip_comp_level 2;
       gzip_proxied any;
       gzip_types      text/plain text/html text/css application/x-javascript text/xml application/xml application/xml+rss text/javascript;
       # Turn off gzip for pre SP2 IE
       gzip_disable      'MSIE [1-6]\.(?!.*SV1)';
       
       
       location = /favicon.ico  {
                root /home/peterbe/djangopeoplenet/static/images;
		expires      30d;
       }
       location = /robots.txt  {
                root /home/peterbe/djangopeoplenet/djangopeople;
		expires      3d;
       }
       

       location ~* ^.+\.(jpg|jpeg|gif|png|ico|css|zip|tgz|gz|rar|bz2|doc|xls|exe|pdf|ppt|tar|mid|midi|wav|bmp|rtf|mov) {
            access_log   off;
            expires      30d;
       }
       
       location ^~ /cache-forever  {
       	       	root /tmp/django-static-forever/djangopeople;
                expires      300d;
       }

       location ^~ /css  {
       		root /home/peterbe/djangopeoplenet/static;
		access_log off;
       }
       location ^~ /img  {
       		root /home/peterbe/djangopeoplenet/static;
       }
       location ^~ /js  {
               	 root /home/peterbe/djangopeoplenet/static;
       }       
       

       location / {

                        # host and port to fastcgi server
                        fastcgi_pass 127.0.0.1:9000;
                        fastcgi_param PATH_INFO $fastcgi_script_name;
                        fastcgi_param REQUEST_METHOD $request_method;
                        fastcgi_param QUERY_STRING $query_string;
                        fastcgi_param SERVER_NAME $server_name;
                        fastcgi_param SERVER_PORT $server_port;
                        fastcgi_param SERVER_PROTOCOL $server_protocol;
                        fastcgi_param CONTENT_TYPE $content_type;
                        fastcgi_param CONTENT_LENGTH $content_length;
			fastcgi_param REMOTE_ADDR $remote_addr;
			#fastcgi_param GEO $geo;
                        fastcgi_pass_header Authorization;
                        fastcgi_intercept_errors off;
        }
}

#server {
#       server_name www.kungfupeople.com;
#       rewrite (.*) http://kungfupeople.com/ permanent;
#}

