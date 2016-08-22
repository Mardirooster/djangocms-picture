# -*- coding: utf-8 -*-

from __future__ import unicode_literals

try:
    import urlparse
except ImportError:
    from urllib import parse as urlparse

from django.conf import settings

from django.conf.urls import patterns, url
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponse
from django.templatetags.static import static
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import csrf_exempt

from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool

from .models import SlidePicture

from cms.models import CMSPlugin
from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool

try:
    from filer.admin.clipboardadmin import ajax_upload as filer_ajax_upload
except ImportError:
    filer_ajax_upload = None
    warnings.warn("Drag and drop functionality is not avalable. "
                  "Please update to django-filer>=1.1.1",
                  Warning)

#from aldryn_bootstrap3 import models, forms, constants

link_fieldset = (
    ('Link', {
        'fields': (
            'link_page', 'link_file', 'link_url', 'link_mailto', 'link_phone',
        ),
        'description': 'Choose one of the link types below.',
    }),
    ('Link options', {
        'fields': (
            ('link_target', 'link_anchor',),
        ),
    }),
)

class SlidePicturePlugin(CMSPluginBase):
    model = SlidePicture
    name = _("SlidePicture")
    render_template = "cms/plugins/slidepicture.html"
    text_enabled = True



    fieldsets = (
        (None, {'fields': (
                'file',
                'use_original_image',
                'title',
                'description',
                #'thumbnail',
                'alt',
        )}),

        ('Advanced', {
            'classes': ('collapse',),
            'fields': (
                'override_width',
                'override_height',
                'classes',
                'img_responsive',
            ),
        }),
    ) + link_fieldset

    def render(self, context, instance, placeholder):
        context.update({'instance': instance})
        if callable(filer_ajax_upload):
            # Use this in template to conditionally enable drag-n-drop.
            context.update({'has_dnd_support': True})
        return context

    def get_thumbnail(self, instance):
        return instance.file.file.get_thumbnail({
            'size': (40, 40),
            'crop': True,
            'upscale': True,
            'subject_location': instance.file.subject_location,
        })

    def icon_src(self, instance):
        if instance.file_id:
            thumbnail = self.get_thumbnail(instance)
            return thumbnail.url
        return ''

    def get_plugin_urls(self):
        urlpatterns = patterns(
            '',
            url(r'^ajax_upload/(?P<pk>[0-9]+)/$', self.ajax_upload,
                name='bootstrap3_image_ajax_upload'),
        )
        return urlpatterns

    @csrf_exempt
    def ajax_upload(self, request, pk):

        """
        Handle drag-n-drop uploads.

        Call original 'ajax_upload' Filer view, parse response and update
        plugin instance file_id from it. Send original response back.
        """
        if not callable(filer_ajax_upload):
            # Do not try to handle request if we were unable to
            # import Filer view.
            raise ImproperlyConfigured(
                "Please, use django-filer>=1.1.1 to get drag-n-drop support")
        filer_response = filer_ajax_upload(request, folder_id=None)

        if filer_response.status_code != 200:
            return filer_response

        try:
            file_id = json.loads(filer_response.content)['file_id']
        except ValueError:
            return HttpResponse(
                json.dumps(
                    {'error': 'received non-JSON response from Filer'}),
                status=500,
                content_type='application/json')
        instance = self.model.objects.get(pk=pk)
        instance.file_id = file_id
        instance.save()
        return filer_response

plugin_pool.register_plugin(SlidePicturePlugin)
