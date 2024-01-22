from http import HTTPStatus
from pytils.translit import slugify

from django.urls import reverse
from django.test import TestCase, Client
from django.contrib.auth import get_user_model

from notes.models import Note
from notes.forms import WARNING


User = get_user_model()


class TestLogic(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Кама Пуля')
        cls.reader = User.objects.create(username='Мага Лезгин')
        cls.note = Note.objects.create(
            title='Заметка № 1',
            text='Текст к заметке',
            author=cls.author,
        )
        cls.form_data = {
            'title': 'Новая заметка',
            'text': 'Новый текст',
            'slug': 'new-note',
        }
        cls.client_author = Client()
        cls.client_reader = Client()
        cls.client_author.force_login(cls.author)
        cls.client_reader.force_login(cls.reader)
        cls.success_url = reverse('notes:success')
        cls.create_url = reverse('notes:add')
        cls.edit_url = reverse('notes:edit', args=(cls.note.slug,))
        cls.delete_url = reverse('notes:delete', args=(cls.note.slug,))

    def test_user_can_create_note(self):
        """
        Тест, что зарегистрированный пользователь может создать заметку,
        его средиректит на страницу 'success'
        и все поля заметки что он создаст - правильные.
        """
        # action
        response = self.client_author.post(
            self.create_url, data=self.form_data)
        note = Note.objects.get(slug=self.form_data['slug'])
        # assertion
        self.assertRedirects(response, self.success_url)
        self.assertEqual(Note.objects.count(), 2)
        self.assertEqual(note.title, self.form_data['title'])
        self.assertEqual(note.text, self.form_data['text'])
        self.assertEqual(note.slug, self.form_data['slug'])
        self.assertEqual(note.author, self.author)

    def test_anonymous_user_cant_create_note(self):
        """
        Тест на то, что анонимный пользователь не может создать заметку,
        его средиректит на страницу логина.
        """
        # arrange
        login_url = reverse('users:login')
        expected_url = f'{login_url}?next={self.create_url}'
        # action
        response = self.client.post(self.create_url, data=self.form_data)
        # assertion
        self.assertRedirects(response, expected_url)
        self.assertEqual(Note.objects.count(), 1)

    def test_not_unique_slug(self):
        """Тест на то, что нельзя создать одинаковый слаг."""
        # arrange
        self.form_data['slug'] = self.note.slug
        # action
        response = self.client_author.post(
            self.create_url, data=self.form_data)
        # assertion
        self.assertFormError(
            response=response,
            form='form',
            field='slug',
            errors=self.note.slug + WARNING
        )
        self.assertEqual(Note.objects.count(), 1)

    def test_empty_slug(self):
        """
        Тест на то, что слаг может создаться автоматически
        и он правильный.
        """
        # arrange
        del self.form_data['slug']
        # action
        response = self.client_author.post(
            self.create_url, data=self.form_data)
        # arrange
        note = Note.objects.order_by('pk').last()
        expexted_slug = slugify(note.title)
        # assertion
        self.assertRedirects(response, self.success_url)
        assert Note.objects.count() == 2
        assert note.slug == expexted_slug

    def test_author_can_edit_note(self):
        """Тест успешного обновления заметки её автором."""
        # action
        response = self.client_author.post(self.edit_url, data=self.form_data)
        self.note.refresh_from_db()
        # assertion
        self.assertRedirects(response, self.success_url)
        self.assertEqual(self.note.title, self.form_data['title'])
        self.assertEqual(self.note.text, self.form_data['text'])
        self.assertEqual(self.note.slug, self.form_data['slug'])

    def test_other_user_cant_edit_note(self):
        """Тест невозможности обновления заметки не её автором."""
        # action
        status_code = self.client_reader.post(
            self.edit_url, data=self.form_data).status_code
        note_from_db = Note.objects.get(pk=self.note.pk)
        # assertion
        self.assertEqual(status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(self.note.title, note_from_db.title)
        self.assertEqual(self.note.text, note_from_db.text)
        self.assertEqual(self.note.slug, note_from_db.slug)

    def test_author_can_delete_note(self):
        """Тест, что автор может удалить свою заметку."""
        # action
        response = self.client_author.post(self.delete_url)
        # assertion
        self.assertRedirects(response, self.success_url)
        assert Note.objects.count() == 0

    def test_other_user_cant_delete_note(self):
        """Тест, что не автор заметки не может её удалить."""
        # action
        status_code = self.client_reader.post(self.delete_url).status_code
        # asserion
        self.assertEqual(status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(Note.objects.count(), 1)
