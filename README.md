# Halite-Bot
Two Sigma's <a href="https://halite.io/">Halite</a> competition ending on Feb 12,2017. Finished as rank 23 out of 1592 (Diamond Tier) 

# Summary
I heard about Halite from a coworker, it sounded pretty interesting so I decided to give it a shot.  I downloaded the python starter package and began messing around with it.  I wanted to make up my own strategies so I avoided reading the forums.  My coworker then gave me the overkill bot and that owned my initial bot.  I was suprised how well the overkill bot was doing with only 50 lines of code.  The goal then became to just over power the overkill bot.  From there on, I pretty much got addicted to Halite.  The highest rank I hit was 13, probably a week before the deadline.  But a lot of people updated their bots with more features toward the end, that seemed to be a lot better than the last updates I did.

# Bot Summary
Here's a quick summary of my bot

* Initialization

I had this commented out with my final submission since it was timing out during the last day, but that was really due to the server issues they were having because everyone were submitting their bots.  This basically get the highest 11 squares (up to 14) that will yield the highest production/strength ratio from the starting square.  I then had two options, whether to tunnel through these 11 squares with all my units or just have the minimum strength required.  For example, if I currently have 5 squares and combining 3 of the squares will be enough to take the 6th square, then the remaining 2 squares will be used to expand somewhere else.

* Attack/Defend

The attack portion is base on the neutrals that are in the front line.  These are squares that have 0 strength and is between my squares and the enemies.  It iterates through each of the neutral squares in front line and numbers my squares adjacent to it.  Up to whatever the variable is set to.  My final submission was set to 6.  Basically, my square right next to the neutral square is numbered as '1', the ones next to this square is numbered '2' and so on up to 6.  This makes each of the numbered squares to flow towards the lower number all the way to the original neutral front line square. 

![Attacking](https://cloud.githubusercontent.com/assets/24849446/23225151/e74bd6b6-f8fe-11e6-8b6e-2a5135c7f37d.jpg "Attacking")

This can cause a build up, since every one of them are just going into a single square, so I added an option where a specified number will be allowed to create another opening.  In my final submission, this number was set to 3.  So if my square that is numbered '3' met the required strength and is next to a neutral, it'll take that neutral square and basically make that a new opening towards the enemy.  This help prevent some build up.

The defend part is similar to attack, but instead of looking for neutrals with 0 strength, it looks for neutrals that is close to an enemy.  For my final submission, this was set to 2.  If an enemy is detected 2 squares away, then these squares will also be numbered, similar to how the attack squares are numbered.  Then it will power up until it reaches the specified strength under the parameters.

* Expand

The remaining squares that are not attacking/defending will then be considered for expanding.  All neutral squares adjacent to my squares (neutral border) are sorted from high to low (base on production/strength).  It iterates that list and then calculates how many squares it needs to take over each of the neutral squares.  For example, the image below shows that 4 of the squares combined will be enough to take over that neutral square.  This takes into account the strength gained in the next 4 moves before taking the neutral square.  The 4 squares will move one at a time, per turn until it reaches the desired neutral square.  It does this to all the neutral border and preventing squares to be assigned towards multiple targets.

![expand](https://cloud.githubusercontent.com/assets/24849446/23225719/e803c77e-f900-11e6-8ce8-82ef2ff81cb0.jpg)

* Evade

The evade part takes squares numbered '1' and '2' into account.  This basically minimizes overkill and avoids splash damages.  It assumes that the enemy will go towards the neutral square in front line, thus only one of the '1' should go towards the neutral and the other should evade, whether it goes toward a different enemy or goes backward (evading).  For example, with the attack image above.  If both the '1' are going to the same neutral square front line, then only one of them will go there.  But it is also possible, with this example that each of the '1' is going to different neutral squares, since there are 2 neutral square front line.  Basically both of them going towards the east. 

* Middle squares

The remaining squares that are not attacking nor expanding, will be the middle squares.  These squares will check if there is an enemy in its north, east, south or west.  If no enemy is detected, then it'll just go towards the closest neutral.

* Manage

Manage prevents squares from going over 255.  If it is, it temporarily sets its direction to STILL, recursively check other squares possibly going to that position and setting those to STILL as well.  All the squares that are STILL will then be analyzed to see if their positions can be swapped.  If a stronger square that is STILL, previously wanted to go to a weaker square that is also STILL, it'll change both its direction and swap their positions.

# Improvements to be made
*With defending, it also prevents attacking (similar to NAP) but it currently just always go to the right.  Once it reaches the desired strength, it wont go towards the enemy but it'll always just go to the right.  This should go to the direction with higher production area.
*Middle squares just go to the nearest neutral square.  It should also go to the direction of higher production squares.
*Need to update evading.  Some scenarios still causes overkill/splash damage.  For example, if an enemy square has neutral front line squares in both east and west with my squares next to it.  If the enemy didnt move and both my squares went towards the neutral front line squares, then both of them will be damaged by the strength of the enemy.
*Update attack style.  It seems that against the top players, even if we started with the same production/territory, they seem to always win.  Maybe since my attack has a funneling formation where as others has more of a uniform attack towards the enemy. 
