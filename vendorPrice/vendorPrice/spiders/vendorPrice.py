#coding=utf-8
import re
import time
import json
import scrapy
from bs4 import BeautifulSoup
from mysql_dal.models.product.product_model import ProductModel

class vendorPrice(scrapy.Spider):

    
    name = "vendorPrice"
    DB_SETTING = [{'host':'vpc-product.cukhkd3vy9hv.us-east-1.rds.amazonaws.com', 'username':'prod_product', 'password':'secret008', 'dbname':'product_db_v2', 'port':3306, 'is_master':True, 'charset':'utf8'}]
    pm = ProductModel(DB_SETTING)

    def __init__(self):

        #self.pat = re.compile("(?<=\"masterProductId\":\")\d+?(?=\")")
        self.bPat = re.compile("(?<=retailPrice\":).+?(?=,)")
        self.pricePat = re.compile("(?<=value=\")\$.+(?=\")")

    def start_requests(self):
        fields = ["pp_id","product_url","product_vendor","product_sku","product_price"]
        start_urls = self.pm.select_product_sku(fields)
        #start_urls = ["https://www.bloomingdales.com/shop/product/?ID=1694326"]

        for info in start_urls:
            if info["product_sku"]:
                if info["product_vendor"] == "BloomingDale\'s":
                    url = "https://www.bloomingdales.com/shop/product/?ID=%s" % info["product_sku"]
                elif info["product_vendor"] == "Zappos":
                    url = "http://www.zappos.com/p/product/%s" % info["product_sku"]
                elif info["product_vendor"] == "Staples":
                    url = "https://www.staples.com/product_%s" % info["product_sku"]
                else:
                    url = None
            else:
                url = info["product_url"]

            if url:
                yield scrapy.Request(url=url,callback=self.parse,meta={"url":url,"vendor":info["product_vendor"],"p_id":info["pp_id"],"product_price":info["product_price"]})

    def exceptionUrl(self,subUrl,vendor):

        with open("eUrl.md","a") as f:

            f.write("%s\t%s\n" % (subUrl,vendor))

    def parse(self,response):
        print "http status is %s  and url is %s" % (str(response.status),response.url)
        #print "********************{}++++++++++++".format(response.meta["proxy"])
        if response.meta["vendor"] == "BloomingDale\'s":
            """
            masterProductId = re.findall(self.pat,response.body)
            print "*********************"
            print masterProductId
            print "65.0" in response.body
            if masterProductId:
                subUrl = "https://www.bloomingdales.com/catalog/product/quickview/?id=%s" % masterProductId[0]
                yield scrapy.Request(url=subUrl,callback=self.bloomingdalesParse,meta={"subUrl":subUrl,"webId":response.meta["url"].split("=")[-1]})
            else:
                self.exceptionUrl(subUrl,response.meta["vendor"])
            """
            price = self.bloomingdalesParse(response)

        if response.meta["vendor"] == "Zappos":
            price = self.zapposParse(response)

        if response.meta["vendor"] == "Staples":
            price = self.staplesParse(response)
        
        updateTime = str(time.time())
        date = time.strftime("%Y-%m-%d",time.localtime(time.time()))
        if price != "null":
            product_price = {"date":date,"update_time":updateTime,"price":price[1:],"symbol":price[0]}
        else:
            product_price = {"date":date,"update_time":updateTime,"price":price,"symbol":""}
        
        jsonPrice = json.loads(response.meta["product_price"])
        jsonPrice.append(product_price)
        print response.meta["p_id"]
        self.pm.update_product_by_pId(response.meta["p_id"],json.dumps(jsonPrice))

    def staplesParse(self,response):
        
        soup = BeautifulSoup(response.body,"lxml")
        content = soup.find_all("span",attrs = {"class":"SEOFinalPrice"})

        if content:
            print "$%s" % content[0].text
            return "$%s" % content[0].text
        else:
            return "null"


    def zapposParse(self,response):

        soup = BeautifulSoup(response.body,"lxml")
        content = soup.find_all("span",attrs = {"class":"price nowPrice"})
        if content:
            print content[0].text
            return content[0].text
        else:
            return "null"

    def bloomingdalesParse(self,response):
        """
        jsonData = json.loads(response.body.replace("\n",""))["overviewMaster"]
        try:
            price = [re.findall(self.pricePat,x["productPrice"])[0] for x in jsonData if x["webId"] == response.meta["webId"]][0]
            return price
        except:
            return "null"
        """
        content = re.findall(self.bPat,response.body)
        if content:
            print "$%s" % content[0]
            return "$%s" % content[0]
        else:
            return "null"
