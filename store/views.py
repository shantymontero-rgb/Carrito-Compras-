from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Product, CartItem
from .serializers import ProductSerializer, CartItemSerializer

# --- Vistas Web ---
def catalog_view(request):
    return render(request, 'store/catalog.html')

def cart_view(request):
    return render(request, 'store/cart.html')

def login_view(request):
    return render(request, 'store/login.html')


# --- Endpoints API ---

class ProductListAPI(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        category = request.query_params.get('category')
        products = Product.objects.all()
        if category:
            products = products.filter(category=category)
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CartListCreateAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        items = CartItem.objects.filter(user=request.user)
        serializer = CartItemSerializer(items, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        product_id = request.data.get('product')
        try:
            quantity = int(request.data.get('quantity', 1))
        except (ValueError, TypeError):
            return Response({'error': 'Cantidad no válida.'}, status=status.HTTP_400_BAD_REQUEST)

        if quantity <= 0:
            return Response({'error': 'La cantidad debe ser mayor a 0.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({'error': 'Producto no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        if product.stock <= 0:
            return Response({'error': f'El producto "{product.name}" está agotado.'}, status=status.HTTP_400_BAD_REQUEST)

        item, created = CartItem.objects.get_or_create(user=request.user, product=product)
        total_requested = quantity if created else (item.quantity + quantity)

        if total_requested > product.stock:
            return Response(
                {'error': f'No hay suficiente stock. Disponibles: {product.stock}. En tu carro tienes: {0 if created else item.quantity}.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        item.quantity = total_requested
        item.save()

        serializer = CartItemSerializer(item)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CartItemDetailAPI(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        try:
            item = CartItem.objects.get(pk=pk, user=request.user)
            item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except CartItem.DoesNotExist:
            return Response({'error': 'Ítem no encontrado.'}, status=status.HTTP_404_NOT_FOUND)