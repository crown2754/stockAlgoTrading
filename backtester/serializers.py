from rest_framework import serializers

class StockDataSerializer(serializers.Serializer):
    # 定義你想傳回前端的欄位
    symbol = serializers.CharField(max_length=10)
    last_price = serializers.FloatField()
    date = serializers.DateField()
    message = serializers.CharField(max_length=100)