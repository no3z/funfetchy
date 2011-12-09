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


import wsgiref.handlers
import random
import urlparse

class RedditSubmissions(db.Model):
  created_date = db.DateTimeProperty(auto_now_add=True)
  json = db.TextProperty()
  data = db.BlobProperty()
  width = db.IntegerProperty()
  height = db.IntegerProperty()
  title = db.StringProperty()
  url = db.StringProperty()
  author = db.StringProperty()
  score = db.IntegerProperty()
  rand = db.FloatProperty()
  star = db.BooleanProperty()

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
    submissions.order('-created_date')
    self.render_to_response('templatehtml/index.html', {
        'subs': submissions,
     })

class FfPass(FfBaseHandler):
  def get(self):
    submissions = db.Query(RedditSubmissions)
    submissions = RedditSubmissions.all()
    submissions.order('-created_date')
    self.render_to_response('templatehtml/webgl.html', {
        'subs': submissions,
        'size': submissions.count(),
        'one': submissions[0]
     })

class FfBest(FfBaseHandler):
  def get(self):
    submissions = db.Query(RedditSubmissions)
    submissions = RedditSubmissions.all().filter('star =',True)
    submissions.order('-created_date')
    self.render_to_response('templatehtml/index.html', {
        'subs': submissions,
     })

class FfUpVote(FfBaseHandler):
    def post(self,pic_key):
        sub = db.get(pic_key)

        if not sub.star:
          sub.star = True
        else:
          sub.star = False
          
        sub.put()
        
        self.redirect('/webgl')
        
class FfServeImage(webapp.RequestHandler):
    def get(self,pic_key):
        image = db.get(pic_key)
        self.response.headers['Content-Type'] = 'image/gif'
        self.response.out.write(image.data)

class FfDelete(webapp.RequestHandler):
  def get(self):
        #DELETE ALL PREVIOUS POSTS
        s = db.Query(RedditSubmissions)
        s = RedditSubmissions.all();
        for j in s:
          if not j.star:
            j.delete()


class FfUpdate(webapp.RequestHandler):
    def get(self,page):
        
        page_json = urlfetch.Fetch('http://www.reddit.com/r/'+page+'.json' )

        print page,page_json.content
        
        obj = json.loads(  page_json.content )

        #print(obj.get('data').get('children'))
        for subs in  obj.get('data').get('children'):
            if not subs['data']['url']:
              continue
            
            path = urlparse.urlparse(subs['data']['url']).path
            ext = os.path.splitext(path)[1]

            print ext
            if not ext or ext == ".gif":
              continue

            title = subs['data']['title']
            if title.find("NSFW") > 0:
              print title, "Discarded"
              continue
            
            tt = subs['data']['url'];
            s = db.Query(RedditSubmissions)
            s = RedditSubmissions.all();
            r = s.filter('url =', tt).fetch(limit=1)
            print title, tt, len(r)
            if len(r) > 0:
              print "Not added: ", tt
              print "\n"
              continue
            
            try:
              image = urlfetch.Fetch(subs['data']['url']).content
              img = images.Image(image)
              img.im_feeling_lucky()
              
              if img.width > 2048 or img.height > 1600:
                continue
              
                
              if img.width > 1024 or img.height > 768:
                img.resize(1024,768)
                
              png_data = img
                
              png_data = img.execute_transforms(images.PNG)
                
              temp = subs['data']['title']
              temp = temp.replace("\"", "\'")
              RedditSubmissions(
                data= png_data,
                width = img.width,
                height = img.height,
                json = str(subs['data']),
                title = temp,
                  url =subs['data']['url'],
                author = subs['data']['author'],
                score = int(subs['data']['score']),
                rand = random.random(),
                star = False,
                    ).put()
              
              print "put"
              
            except Exception,e:
              print e
              
            self.redirect('/')
                
    #self.render_to_response('templatehtml/upload.html', {'subs': sub })
    

def main():
  url_map = [
             ('/delete', FfDelete),
             ('/best', FfSlideshow),
             ('/webgl', FfPass),
             ('/image/([-\w]+)', FfServeImage),
             ('/upvote/([-\w]+)', FfUpVote),
             ('/update/([-\w]+)', FfUpdate),
             ('/', FfBest)]
             
  application = webapp.WSGIApplication(url_map,debug=True)
  wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
  main()
