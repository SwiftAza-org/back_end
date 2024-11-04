from ..database.mongodb import mongo


class Review:
    @staticmethod
    def create(data):
        return mongo.db.reviews.insert_one(data)

    @staticmethod
    def get_all():
        return list(mongo.db.reviews.find())
