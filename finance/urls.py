from django.urls import path
from . import views

urlpatterns = [

    path("payment/", views.record_payment, name="record_payment"),
    path("pay-fees/<int:student_id>/", views.pay_fees, name="pay_fees"),

]

