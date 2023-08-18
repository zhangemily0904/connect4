from django.db import models
from django.contrib.auth.models import User
 
class Room(models.Model):
   room_id = models.IntegerField(default=-1) # globally unique room id 
   player_1 = models.ForeignKey(User, default=None, on_delete=models.PROTECT, related_name="player_1")
 #models.IntegerField() # user id of the first player
   player_2 = models.ForeignKey(User, default=None, on_delete=models.PROTECT, related_name="player_2", null=True)
#models.IntegerField() # user id of the second player
   turn = models.IntegerField(default=1) 
   board = models.CharField(max_length=2000)
   status = models.CharField(max_length=200, default="")
   timeLeft = models.IntegerField(default=120) 
   challenge = models.ForeignKey(User, default=None, on_delete=models.PROTECT, related_name="challenge", null=True)

class Profile(models.Model):
   user = models.OneToOneField(User, on_delete=models.PROTECT)
   token_picture = models.FileField(blank=True)
   profile_picture = models.FileField(blank=True)
   nickname = models.CharField(max_length=50)
   bio = models.CharField(max_length=200)
   wins = models.IntegerField(default=0) 
   room = models.ForeignKey(Room, default=None, on_delete=models.PROTECT, related_name="room", null=True)
   content_type = models.CharField(max_length=50, default="")
   following = models.ManyToManyField(User, related_name="followers")