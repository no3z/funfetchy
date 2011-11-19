from __future__ import with_statement
from google.appengine.api import files

import os

from google.appengine.dist import use_library
use_library('django', '0.96')

from google.appengine.api import images
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.api import urlfetch
from django.utils import simplejson as json
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers

import urllib
import wsgiref.handlers
import random
import urlparse

class RedditSubmissions(db.Model):
  created_date = db.DateTimeProperty(auto_now_add=True)
  json = db.TextProperty()
  data = db.BlobProperty()
  title = db.StringProperty()
  url = db.StringProperty()
  author = db.StringProperty()
  score = db.IntegerProperty()
  rand = db.FloatProperty()

class FfBaseHandler(webapp.RequestHandler):
  def template_path(self, filename):
    return os.path.join(os.path.dirname(__file__), filename)

  def render_to_response(self, filename, template_args):
    template_args.setdefault('current_uri', self.request.uri)
    self.response.out.write(
        template.render(self.template_path(filename), template_args))


class FfSlideshow(FfBaseHandler):
  def get(self):
    submissions = db.Query(RedditSubmissions)
    submissions = RedditSubmissions.all()
    
    self.render_to_response('templatehtml/index.html', {
        'subs': submissions,
     })


class FfServeImage(webapp.RequestHandler):
    def get(self,pic_key):
        image = db.get(pic_key)
        self.response.headers['Content-Type'] = 'image/png'
        self.response.out.write(image.data)


class FfUpdate(webapp.RequestHandler):
    def get(self):
        self.response.out.write('<html><body>')
        self.response.out.write('<form action="/update" method="POST" enctype="multipart/form-data">')
        self.response.out.write('''Upload File: <input type="file" name="file"><br> <input type="submit"
         name="submit" value="Submit"> </form></body></html>''')


    def post(self):
        page_json = urlfetch.Fetch("http://www.reddit.com/r/wtf.json" )
        obj = json.loads(  page_json.content )
        #obj = json.loads(  urlfetch.Fetch("../media/funny.json" ).content )
        print(obj.get('data').get('children'))
        for subs in  obj.get('data').get('children')[:5]:
            print subs['data']['title'], subs['data']

            if not subs['data']['url']:
              continue

            path = urlparse.urlparse(subs['data']['url']).path
            ext = os.path.splitext(path)[1]

            if not ext:
              continue

            image = urlfetch.Fetch(subs['data']['url']).content
            
            img = images.Image(image)
            img.im_feeling_lucky()

            png_data = img.execute_transforms(images.PNG)

            try:
                RedditSubmissions(
                    data= png_data,
                    json = str(subs['data']),
                    title = subs['data']['title'],
                    url =subs['data']['url'],
                    author = subs['data']['author'],
                    score = int(subs['data']['score']),
                    rand = random.random(),
                    ).put()

                print "put"

            except Exception,e:
                print e

    sub = db.Query(RedditSubmissions)
    sub = RedditSubmissions.all()
    
    #self.render_to_response('templatehtml/upload.html', {'subs': sub })


def main():
  url_map = [('/update', FfUpdate),
             ('/image/([-\w]+)', FfServeImage),
             ('/', FfSlideshow)]
             
  application = webapp.WSGIApplication(url_map,debug=True)
  wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
  main()