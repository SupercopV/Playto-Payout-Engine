from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
from .services import PayoutService
from .serializers import PayoutSerializer, PayoutCreateSerializer, BalanceSerializer
from .models import Payout

class MerchantBalanceView(APIView):
    def get(self, request, merchant_id):
        balances = PayoutService.get_balances(merchant_id)
        serializer = BalanceSerializer(balances)
        return Response(serializer.data)

class PayoutCreateView(APIView):
    def post(self, request):
        idempotency_key = request.headers.get('Idempotency-Key')
        if not idempotency_key:
            return Response({"error": "Idempotency-Key header is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = PayoutCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            payout, created = PayoutService.create_payout(
                merchant_id=serializer.validated_data['merchant_id'],
                amount_paise=serializer.validated_data['amount_paise'],
                idempotency_key=idempotency_key
            )
            
            response_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
            return Response(PayoutSerializer(payout).data, status=response_status)
            
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": "An unexpected error occurred"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PayoutListView(APIView):
    def get(self, request, merchant_id):
        payouts = Payout.objects.filter(merchant_id=merchant_id).order_by('-created_at')
        serializer = PayoutSerializer(payouts, many=True)
        return Response(serializer.data)
