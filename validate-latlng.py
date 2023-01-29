#!/usr/bin/env python3                                                                                                         

# ボーリングデータの緯度経度入力ミスの確認プログラム                                                                           
#       XMLファイルの緯度経度と                                                                                                
#       調査位置住所からgeocoderで求めた緯度経度と比較                                                                         
#       OpenStreetMap のGeoCoder では、川の名前で始まるような                                                                  
#       住所が多く含まれているので、住所からは緯度経度を                                                                       
#       得られないことが多い。                                                                                                 

import requests
import csv
import re
from bs4 import BeautifulSoup
import geocoder
import math

# ボーリングデータのURL                                                                                                        
url = "https://raw.githubusercontent.com/GeoFUKUI/jiban-opendata/main/filelist.csv"

# 緯度経度ミスとみなす緯度経度距離                                                                                             
err_max = 0.001

res = requests.get( url )

if res.ok :
    for line in res.text.splitlines() :
        url , type , size = line.split(',')
        if re.match( '.*/DATA/BED\d\d\d\d\.XML$' , url ) :
             xml_url = "https://raw.githubusercontent.com/GeoFUKUI/jiban-opendata/main/data/" + url
             xml_res = requests.get( xml_url )
             if xml_res.ok :
                 soup = BeautifulSoup( xml_res.text , 'xml' )
                 # <経度緯度情報><{緯度|経度}_{度|分|秒}>                                                                      
                 for lat_lng in soup.find_all( '経度緯度情報' ) :
                     # <調査位置><調査位置住所>                                                                                
                     lat_deg = int( lat_lng.find( '緯度_度' ).string )
                     lat_min = int( lat_lng.find( '緯度_分' ).string )
                     lat_sec = float( lat_lng.find( '緯度_秒' ).string )
                     lng_deg = int( lat_lng.find( '経度_度' ).string )
                     lng_min = int( lat_lng.find( '経度_分' ).string )
                     lng_sec = float( lat_lng.find( '経度_秒' ).string )
                     lat = lat_deg + lat_min / 60 + lat_sec / 3600
                     lng = lng_deg + lng_min / 60 + lng_sec / 3600
                     # print( lat )                                                                                            

                 # 住所の文字列を加工                                                                                          
                 addr = soup.find( '調査位置住所' ).string
                 addr = re.sub( '地係$' , '' , addr )
                 addr = re.sub( '　' , '' , addr )
                 # XX町〜XX町は後半削除                                                                                        
                 addr = re.sub( '(～|から).*$' , '' , addr )
                 addr = re.sub( '^.*福井県' , '' , addr )
                 # ()を含む部分を消す                                                                                          
                 addr = re.sub( '（.*）' , '' , addr )
                 addr = re.sub( '\(.*\)' , '' , addr )
                 addr = "福井県" + addr
                 #print( addr )                                                                                                

                 # Geocoderで住所から緯度経度をもとめる                                                                        
                 geo_addr = geocoder.osm( addr , timeout = 5.0 )
                 if geo_addr is None :
                     print( "None" )
                 elif isinstance( geo_addr.latlng , list ) :
                     # 住所から求めた緯度経度                                                                                  
                     geo_lat , geo_lng = geo_addr.latlng
                     # 2つの緯度経度間の距離(本来なら球面距離の計算が必要)                                                     
                     err = math.sqrt( (lat - geo_lat)**2 + (lng - geo_lng)**2 )
                     # 距離が一定量以上なら間違いあり                                                                          
                     if err > err_max :
                         print( "(%f,%f)-(%f,%f)-%s" % ( lat , lng , geo_lat , geo_lng , addr ) )
                 else :
                     # 緯度経度が分からなかった                                                                                
                     print( "(%f,%f)-(xxx,xxx)-%s" % ( lat , lng , addr ) )
