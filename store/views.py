from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from django.db.models import Sum, F
from django.contrib.auth.models import User
from .models import Product, CartItem
from .serializers import ProductSerializer, CartItemSerializer

# --- Vistas Web ---
def catalog_view(request):
    return render(request, 'store/catalog.html')

def cart_view(request):
    return render(request, 'store/cart.html')

def login_view(request):
    return render(request, 'store/login.html')

def dashboard_view(request):
    return render(request, 'store/dashboard.html')


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
        total_items = sum(item.quantity for item in items)
        return Response({
            'items': serializer.data,
            'total_items_count': total_items
        }, status=status.HTTP_200_OK)

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

        # Retornamos el total global para actualizar el badge del frontend
        all_user_items = CartItem.objects.filter(user=request.user)
        total_items = sum(i.quantity for i in all_user_items)

        return Response({
            'item': CartItemSerializer(item).data,
            'total_items_count': total_items,
            'message': f'Tienes {total_requested} unidad(es) de este producto en el carro.'
        }, status=status.HTTP_201_CREATED)


class CartItemDetailAPI(APIView):
    permission_classes = [IsAuthenticated]

    # PUT: Editar la cantidad de un ítem existente en el carro
    def put(self, request, pk):
        try:
            item = CartItem.objects.get(pk=pk, user=request.user)
        except CartItem.DoesNotExist:
            return Response({'error': 'Ítem no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            new_quantity = int(request.data.get('quantity', 1))
        except (ValueError, TypeError):
            return Response({'error': 'Cantidad no válida.'}, status=status.HTTP_400_BAD_REQUEST)

        if new_quantity <= 0:
            item.delete()
            return Response({'message': 'Producto removido del carro.'}, status=status.HTTP_200_OK)

        if new_quantity > item.product.stock:
            return Response(
                {'error': f'Supera el stock disponible. El máximo es {item.product.stock}.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        item.quantity = new_quantity
        item.save()

        all_user_items = CartItem.objects.filter(user=request.user)
        total_items = sum(i.quantity for i in all_user_items)

        return Response({
            'item': CartItemSerializer(item).data,
            'total_items_count': total_items,
            'message': 'Cantidad actualizada exitosamente.'
        }, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        try:
            item = CartItem.objects.get(pk=pk, user=request.user)
            item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except CartItem.DoesNotExist:
            return Response({'error': 'Ítem no encontrado.'}, status=status.HTTP_404_NOT_FOUND)


# --- Endpoint Exclusivo de Administrador (Dashboard) ---
class AdminDashboardStatsAPI(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        total_products = Product.objects.count()
        low_stock_products = Product.objects.filter(stock__lte=3)
        total_inventory_value = Product.objects.aggregate(total=Sum(F('price') * F('stock')))['total'] or 0
        total_cart_reservations = CartItem.objects.count()
        total_users = User.objects.count()

        return Response({
            'total_products': total_products,
            'low_stock_count': low_stock_products.count(),
            'low_stock_items': ProductSerializer(low_stock_products, many=True).data,
            'total_inventory_value': total_inventory_value,
            'total_cart_reservations': total_cart_reservations,
            'total_users': total_users
        }, status=status.HTTP_200_OK)


# Endpoint auxiliar para conocer el perfil del usuario actual (si es admin o no)
class CurrentUserAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            'username': request.user.username,
            'is_staff': request.user.is_staff
        })