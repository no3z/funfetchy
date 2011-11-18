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
  json = db.StringProperty()
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
    print (submissions.count())

    self.render_to_response('templatehtml/index.html', {
        'subs': submissions,
      })


class FfUpdate(FfBaseHandler):

  def get(self):
    r = reddit.Reddit(user_agent="redfunfetcher")
    l = list(r.get_subreddit("funny").get_top(limit=300))



    for s in l:
        print s,int(str(s.url).find(".jpg"))
        if int(str(s.url).find(".jpg")) > 0:
            img_data = db.Blob(urlfetch.Fetch(str(s.url)).content)

        if img_data == None:
            continue
        try:
            img = images.Image(img_data)
            jpg_data = img.execute_transforms(images.JPG)
            RedditSubmissions(
            data = jpg_data,title = s.title,
            url = s.url,  author = s.author,
            json = db.StringProperty(),   rand = random.random()).put()
        except:
            self.error(400)
            self.response.out.write('Sorry, the image provided was too large for us to process.')

    sub = db.Query(RedditSubmissions)
    sub = RedditSubmissions.all()
    
    self.render_to_response('templatehtml/upload.html', {'subs': sub })


def main():
  url_map = [('/update', FfUpdate),
             ('/', FfSlideshow)]
             
  application = webapp.WSGIApplication(url_map,debug=True)
  wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
  main()