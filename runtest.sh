#HTTPie

http POST localhost:5000/sign-up name=test1 email=test1@test.com password=1234
http POST localhost:5000/sign-up name=test2 email=test2@test.com password=1234
http POST localhost:5000/sign-up name=test3 email=test3@test.com password=1234
http POST localhost:5000/follow follow=2 id=1
http POST localhost:5000/follow follow=3 id=1
http POST localhost:5000/follow follow=1 id=2
http POST localhost:5000/follow follow=1 id=3
http POST localhost:5000/follow follow=2 id=3
http POST localhost:5000/unfollow unfollow=3 id=1
http POST localhost:5000/tweet id=1 tweet='1의 트윗1'
http POST localhost:5000/tweet id=1 tweet='1의 트윗2'
http POST localhost:5000/tweet id=2 tweet='2의 트윗1'
http POST localhost:5000/tweet id=3 tweet='3의 트윗1'
http POST localhost:5000/tweet id=3 tweet='3의 트윗2'
http POST localhost:5000/tweet id=1 tweet='3의 트윗3'


