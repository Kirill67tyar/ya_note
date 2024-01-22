from django.urls import reverse
from django.test import TestCase
from django.contrib.auth import get_user_model

from notes.models import Note


User = get_user_model()


class TestContent(TestCase):

    NOTES_LIST_URL = reverse('notes:list')

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Кама Пуля')
        cls.reader = User.objects.create(username='Мага Лезгин')
        cls.note = Note.objects.create(
            title='Заметка № 1',
            text='Текст к заметке',
            author=cls.author,
        )
        cls.note_slug = cls.note.slug

    def test_notes_list_for_different_users(self):
        """
        Тест, заметка доступна только её автору,
        и она есть в конексте, в списке object_list.
        """
        # arrange
        users = [
            (self.author, self.assertIn),
            (self.reader, self.assertNotIn),
        ]
        for user, assertion in users:
            self.client.force_login(user)
            with self.subTest(user=user, assertion=assertion):
                # action
                response = self.client.get(self.NOTES_LIST_URL)
                object_list = response.context['object_list']
                # assertion
                assertion(self.note, object_list)

    def test_pages_contains_form(self):
        """
        Тест, на страницы создания и редактирования заметки,
        передаются формы.
        """
        # arrange
        urls = [
            ('notes:add', None,),
            ('notes:edit', (self.note_slug,),),
        ]
        for view_name, args in urls:
            self.client.force_login(self.author)
            with self.subTest(view_name=view_name, args=args):
                url = reverse(view_name, args=args)
                # action
                response = self.client.get(url)
                # assertion
                self.assertIn('form', response.context)
