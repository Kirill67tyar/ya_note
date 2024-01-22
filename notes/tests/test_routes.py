from http import HTTPStatus

from django.urls import reverse
from django.test import TestCase
from django.contrib.auth import get_user_model

from notes.models import Note


User = get_user_model()


class TestRoutes(TestCase):

    STATUS_OK = HTTPStatus.OK

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

    def test_pages_availability_for_anonymous_user(self):
        """
        Тест страницы: главная, авторизации, выхода, регистрации
        доступны анонимному пользователю.
        """
        # arrange
        urls = (
            'notes:home',
            'users:login',
            'users:logout',
            'users:signup',
        )
        for view_name in urls:
            with self.subTest(view_name=view_name):
                # action
                status_code = self.client.get(reverse(view_name)).status_code
                # assertion
                self.assertEqual(
                    status_code,
                    self.STATUS_OK,
                    msg=(f'Получили статус код {status_code},'
                         'Ожидаемый статус код 200')
                )

    def test_pages_availability_for_different_users(self):
        """
        Тест страницы: просмотра одной, редактирования, удаления
        заметки доступны только её автору.
        """
        # arrange
        user_status = (
            (self.author, self.STATUS_OK,),
            (self.reader, HTTPStatus.NOT_FOUND,),
        )
        urls = [
            ('notes:detail', (self.note_slug,),),
            ('notes:edit', (self.note_slug,),),
            ('notes:delete', (self.note_slug,),),
        ]
        for user, exptected_status_code in user_status:
            self.client.force_login(user)
            for view_name, args in urls:
                with self.subTest(user=user, view_name=view_name, args=args):
                    url = reverse(view_name, args=args)
                    # action
                    status_code = self.client.get(url).status_code
                    # assertion
                    self.assertEqual(
                        status_code,
                        exptected_status_code,
                        msg=(f'Статус код запроса {status_code},'
                             f'ожидаемый статус код {exptected_status_code}')
                    )

    def test_pages_availability_for_auth_user(self):
        """
        Тест страницы: просмотра списка, создания
        заметки доступны авторизованному пользователю.
        """
        # arrange
        urls = [
            'notes:add',
            'notes:list',
            'notes:success',
        ]
        self.client.force_login(self.author)
        for view_name in urls:
            with self.subTest(view_name=view_name):
                # action
                status_code = self.client.get(reverse(view_name)).status_code
                # assertion
                self.assertEqual(
                    status_code,
                    self.STATUS_OK,
                    msg=(f'Статус код запроса {status_code},'
                         f'ожидаемый статус код {self.STATUS_OK}')
                )

    def test_redirects(self):
        """
        Тест редиректа страницы: просмотра списка/одной, создания,
        изменения, удаления, для анонимному пользователю.
        """
        # arrange
        login_url = reverse('users:login')
        urls = [
            ('notes:add', None,),
            ('notes:list', None,),
            ('notes:success', None,),
            ('notes:edit', (self.note_slug,),),
            ('notes:detail', (self.note_slug,),),
            ('notes:delete', (self.note_slug,),),
        ]
        for view_name, args in urls:
            url = reverse(view_name, args=args)
            redirect_url = f'{login_url}?next={url}'
            with self.subTest(view_name=view_name):
                # action
                response = self.client.get(url)
                # assertion
                self.assertRedirects(
                    response=response,
                    expected_url=redirect_url,
                )
