from django.contrib.auth.views import \
 LoginView, LogoutView, PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import login
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.shortcuts import get_object_or_404, resolve_url, redirect
from django.http import HttpResponse
from django.views import generic

from .tokens import account_activation_token
from .forms import RegistrationForm
from store.models import Product
from .models import CustomUser, Review, OrderProduct


class CustomLoginView(LoginView):
    """
    View for user to login
    """
    template_name = 'authentication/user/login.html'
    redirect_authenticated_user = True
    next_page = 'authentication:profile'


class CustomLogoutView(LoginRequiredMixin, LogoutView):
    """
    View for user to logout
    """
    next_page = 'store:index'


class UserRegistrationFormView(generic.edit.FormView):
    """
    View for new User models creation
    Creates model with is_active = False and send an
    email to activate account
    """
    template_name = 'authentication/user/registration.html'
    form_class = RegistrationForm
    success_url = 'store:index'

    def form_valid(self, form):
        form = self.get_form()
        user = form.save()
        current_site = get_current_site(self.request)
        subject = 'Activate your Account'
        message = render_to_string('authentication/user_activation_email.html', {
            'user': user,
            'domain': current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': account_activation_token.make_token(user),
        })
        user.email_user(subject=subject, message=message)
        return super().form_valid(form)

    def get_success_url(self):
        return resolve_url(str(self.success_url))


class UserActivationView(generic.base.View):
    """
    User activation view
    """
    def get(self, *args, **kwargs):
        try:
            uid = force_str(urlsafe_base64_decode(self.kwargs.get('uidb64')))
            user = CustomUser.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, user.DoesNotExist):
            user = None
        if user is not None and account_activation_token.check_token(user, self.kwargs.get('token')):
            user.is_active = True
            user.save()
            login(self.request, user)
            return redirect('authentication:profile')
        else:
            return HttpResponse('2')


class UserProfileView(generic.list.ListView, LoginRequiredMixin):
    """
    Return list of Orders that user authenticated has made
    """
    template_name = 'authentication/user/profile.html'
    context_object_name = 'Orders'

    def get_queryset(self):
        intermediate_query = OrderProduct.objects.filter(
            order__user=self.request.user
        ).select_related(
            'order'
        ).select_related(
            'product'
        )

        query = {}

        for item in intermediate_query:
            if item.order in query:
                query[item.order].append(item)
            else:
                query[item.order] = [item]

        return query


class UserReviewView(LoginRequiredMixin, generic.list.ListView):
    """
    Return list of Reviews that user authenticated has made
    """
    template_name = 'authentication/user/profile_review.html'
    context_object_name = 'Reviews'

    def get_queryset(self):
        query = Review.objects.filter(user__id=self.request.user.id)

        return query


class CustomPasswordResetView(PasswordResetView):
    """
    Resets the password and send and email with confirmation link
    """
    template_name = 'authentication/user/password_reset_form.html'
    email_template_name = "authentication/user/password_reset_email.html"
    success_url = reverse_lazy('authentication:password_reset_done')


class CustomPasswordResetDoneView(PasswordResetDoneView):
    """
    Succes url redirect on password reset
    """
    template_name = 'authentication/user/password_reset_done.html'


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    """
    Changes password of concrete user
    """
    template_name = 'authentication/user/password_reset_confirm.html'
    success_url = reverse_lazy('authentication:password_reset_complete')


class CustomPassworwResetCompleteView(PasswordResetCompleteView):
    """
    Success url redirect after password reset
    """
    template_name = 'authentication/user/password_reset_complete.html'


class ReviewCreateView(LoginRequiredMixin, generic.edit.CreateView):
    """
    Instantiate Review
    """
    model = Review
    fields = ['review_pros', 'review_cons', 'review_commentary', 'rating']
    template_name = 'authentication/reviews/add_review.html'

    def get(self, request, *args, **kwargs):
        product = get_object_or_404(Product, slug=self.kwargs['slug'])
        product_reviews = product.review_set.all()
        users_already_reviewed = CustomUser.objects.filter(review__in=product_reviews)

        if request.user in users_already_reviewed:
            return redirect(product)

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = get_object_or_404(Product.objects.filter(slug=self.kwargs.get('slug')))
        context.update({
            'product': product,
        })
        return context

    def form_valid(self, form):
        review = form.save(commit=False)
        product = get_object_or_404(Product, slug=self.kwargs.get('slug'))
        review.product = product
        review.user = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        product = get_object_or_404(Product, slug=self.kwargs.get('slug'))
        return product.get_absolute_url()


class UpdateReviewView(LoginRequiredMixin, generic.edit.UpdateView):
    """
    Updates review
    """
    fields = ['review_pros', 'review_cons', 'review_commentary', 'rating']
    template_name = 'authentication/reviews/update_review.html'

    def get_object(self, queryset=None):
        review = get_object_or_404(Review.objects.filter(
            id=self.kwargs.get('id'), user=self.request.user
            ).select_related('product')
        )
        return review

    def get_success_url(self):
        product = self.get_object().product
        return product.get_absolute_url()


class DeleteReviewView(LoginRequiredMixin, generic.edit.DeleteView):
    """
    Deletes review
    """
    template_name = 'authentication/reviews/delete_review.html'

    def get_object(self):
        review = get_object_or_404(Review.objects.filter(
            id=self.kwargs.get('id'), user=self.request.user
            ).select_related('product')
        )
        return review

    def get_success_url(self):
        product = self.get_object().product
        return product.get_absolute_url()
