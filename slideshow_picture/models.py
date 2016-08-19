# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

from functools import partial
import collections

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.html import strip_tags
from django.utils.translation import ugettext_lazy as _, ungettext

import django.forms.models

from cms.models.pluginmodel import CMSPlugin
import cms.models
import cms.models.fields

from djangocms_attributes_field.fields import AttributesField
import djangocms_text_ckeditor.fields
import filer.fields.file
import filer.fields.image
import filer.fields.folder
from aldryn_bootstrap3.models import LinkMixin
import aldryn_bootstrap3.model_fields as model_fields
import aldryn_bootstrap3.constants as constants


try:
    from cms.models import get_plugin_media_path
except ImportError:
    def get_plugin_media_path(instance, filename):
        """
        See cms.models.pluginmodel.get_plugin_media_path on django CMS 3.0.4+
        for information
        """
        return instance.get_media_path(filename)
from cms.utils.compat.dj import python_2_unicode_compatible



@python_2_unicode_compatible
class SlidePicture(CMSPlugin, LinkMixin):
    """
    A Picture with or without a link.
    """
    file = filer.fields.image.FilerImageField(
        verbose_name=_("file"),
        blank=False,
        null=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    alt = model_fields.MiniText(
        _("alt"),
        blank=True,
        default='',
    )
    title = model_fields.MiniText(
        _("title"),
        blank=True,
        default='',
    )
    description = model_fields.MiniText(_("description"),blank=True,default='',)
    use_original_image = models.BooleanField(
        _("use original image"),
        blank=True,
        default=False,
        help_text=_(
            "use the original full-resolution image (no resizing)."
        )
    )
    override_width = models.IntegerField(
        _("override width"),
        blank=True,
        null=True,
        help_text=_(
            'if this field is provided it will be used to scale image.'
        )
    )
    override_height = models.IntegerField(
        _("override height"),
        blank=True,
        null=True,
        help_text=_(
            'if this field is provided it will be used to scale image. '
            'If aspect ration is selected - height will be calculated '
            'based on that.'
        )
    )
    aspect_ratio = models.CharField(
        _("aspect ratio"),
        max_length=10,
        blank=True,
        default='',
        choices=constants.ASPECT_RATIO_CHOICES
    )
    thumbnail = models.BooleanField(
        _("thumbnail"),
        default=False,
        blank=True,
        help_text="add the 'thumbnail' border",
    )
    shape = models.CharField(
        _('shape'),
        max_length=64,
        blank=True,
        default='',
        choices=(
            ('rounded', 'rounded'),
            ('circle', 'circle'),
        )
    )

    classes = model_fields.Classes()
    img_responsive = models.BooleanField(
        verbose_name='class: img-responsive',
        default=True,
        blank=True,
        help_text='whether to treat the image as using 100% width of the '
                  'parent container (sets the img-responsive class).'
    )

    def __str__(self):
        txt = 'Image'

        if self.file_id and self.file.label:
            txt = self.file.label
        return txt

    def srcset(self):
        if not self.file:
            return []
        items = collections.OrderedDict()
        if self.aspect_ratio:
            aspect_width, aspect_height = tuple([int(i) for i in self.aspect_ratio.split('x')])
        else:
            aspect_width, aspect_height = None, None
        for device in constants.DEVICES:
            if self.override_width:
                width = self.override_width
            else:
                # TODO: should this should be based on the containing col size?
                width = device['width_gutter']
            width_tag = str(width)
            if aspect_width is not None and aspect_height is not None:
                height = int(float(width)*float(aspect_height)/float(aspect_width))
                crop = True
            else:
                if self.override_height:
                    height = self.override_height
                else:
                    height = 0
                crop = False
            items[device['identifier']] = {
                'size': (width, height),
                'size_str': "{}x{}".format(width, height),
                'width_str': "{}w".format(width),
                'subject_location': self.file.subject_location,
                'upscale': True,
                'crop': crop,
                'aspect_ratio': (aspect_width, aspect_height),
                'width_tag': width_tag,
            }

        return items
