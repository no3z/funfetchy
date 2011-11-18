import os

from google.appengine.dist import use_library
use_library('django', '0.96')

from google.appengine.api import images
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.api import urlfetch

import wsgiref.handlers
import random
import reddit


class RedditSubmissions(db.Model):
  created_date = db.DateTimeProperty(auto_now_add=True)
  data = db.BlobProperty()
  title = db.StringProperty()
  url = db.StringProperty()
  author = db.StringProperty()
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


class FfUpdate(FfBaseHandler):

  def get(self):
    r = reddit.Reddit(user_agent="redfunfetcher2")
    l = list(r.get_subreddit("funny").get_top(limit=20))

 
    for s in l:
        if int(str(s.url).find(".jpg")) > 0:
            print s,s.title,s.url

            image = urlfetch.Fetch(str(s.url)).content

            jpg = db.Blob(images.execute_transforms(image.JPEG))

            try:
                RedditSubmissions(
                data = jpg,
                title = s.title,
                url = s.url,
                author = s.author.user_name,
                rand = random.random()).put()

            except Exception,e:
                print e
                self.response.out.write('Sorry, the image provided was too large for us to process.')
                continue

    sub = db.Query(RedditSubmissions)
    sub = RedditSubmissions.all()
    
    #self.render_to_response('templatehtml/upload.html', {'subs': sub })


def main():
  url_map = [('/update', FfUpdate),
             ('/', FfSlideshow)]
             
  application = webapp.WSGIApplication(url_map,debug=True)
  wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
  main()