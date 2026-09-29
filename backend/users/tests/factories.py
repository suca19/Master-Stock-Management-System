import factory

from users.models import User

DEFAULT_PASSWORD = 'Test!Passw0rd'


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        skip_postgeneration_save = True

    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda u: f'{u.username}@example.com')
    first_name = 'Test'
    last_name = factory.Sequence(lambda n: f'User{n}')
    role = User.STAFF

    @factory.post_generation
    def password(obj, create, extracted, **kwargs):
        obj.set_password(extracted or DEFAULT_PASSWORD)
        if create:
            obj.save(update_fields=['password'])
