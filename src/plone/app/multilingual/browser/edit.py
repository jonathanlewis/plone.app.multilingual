from plone.dexterity.browser.edit import DefaultEditForm
from plone.z3cform import layout
from Products.CMFCore.utils import getToolByName
from Acquisition import aq_inner
from AccessControl.SecurityManagement import getSecurityManager
from zope.component import getMultiAdapter

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from plone.app.multilingual.browser.selector import LanguageSelectorViewlet
from plone.app.i18n.locales.browser.selector import LanguageSelector

from plone.multilingualbehavior.interfaces import ILanguageIndependentField

class MultilingualEditForm(DefaultEditForm):

    babel = ViewPageTemplateFile("dexterity_edit.pt")

    def languages(self):
        context = aq_inner(self.context)

        ls = LanguageSelector(self.context, self.request, None, None)
        ls.update()
        results = ls.languages()

        supported_langs = [v['code'] for v in results]
        missing = set([str(c) for c in supported_langs])

        lsv = LanguageSelectorViewlet(self.context, self.request, None, None)
        translations = lsv._translations(missing)

        # We want to see the babel_view
        append_path = ('','babel_view',)
        _checkPermission = getSecurityManager().checkPermission

        non_viewable = set()
        for data in results:
            code = str(data['code'])
            data['translated'] = code in translations.keys()

            appendtourl = '/'.join(append_path)

            if data['translated']:
                trans, direct, has_view_permission = translations[code]
                if not has_view_permission:
                    # shortcut if the user cannot see the item
                    non_viewable.add((data['code']))
                    continue

                state = getMultiAdapter((trans, self.request),
                        name='plone_context_state')
                try:
                    data['url'] = state.canonical_object_url() + appendtourl
                except AttributeError:
                    data['url'] = context.absolute_url() + appendtourl
            else:
                has_view_permission = bool(_checkPermission('View', context))
                # Ideally, we should also check the View permission of default
                # items of folderish objects.
                # However, this would be expensive at it would mean that the
                # default item should be loaded as well.
                #
                # IOW, it is a conscious decision to not take in account the
                # use case where a user has View permission a folder but not on
                # its default item.
                if not has_view_permission:
                    non_viewable.add((data['code']))
                    continue

                state = getMultiAdapter((context, self.request),
                        name='plone_context_state')
                try:
                    data['url'] = state.canonical_object_url() + appendtourl
                except AttributeError:
                    data['url'] = context.absolute_url() + appendtourl

        # filter out non-viewable items
        results = [r for r in results if r['code'] not in non_viewable]
        return results

    def portal_url(self):
        portal_tool = getToolByName(self.context, 'portal_url', None)
        if portal_tool is not None:
            return portal_tool.getPortalObject().absolute_url()
        return None

    def render(self):
        for field in self.fields.keys():
            if field in self.schema:
                if ILanguageIndependentField.providedBy(self.schema[field]):
                    self.widgets[field].addClass('languageindependent')
        self.babel_content = super(MultilingualEditForm,self).render()
        return self.babel()


DefaultMultilingualEditView = layout.wrap_form(MultilingualEditForm)