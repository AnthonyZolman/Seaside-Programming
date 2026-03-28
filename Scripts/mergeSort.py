def merge(left, right):
   # Merge two sorted lists and keep only the top 5 highest elements
   result = []
   i, j = 0, 0
   while i < len(left) and j < len(right):
       if left[i] > right[j]: # Sorting in descending order
           result.append(left[i])
           i += 1
       else:
           result.append(right[j])
           j += 1
       # Keep the result limited to 5 elements
       #if len(result) > 5:
       #    result.pop()
   # Add remaining elements from left or right (if any)
   result.extend(left[i:])
   result.extend(right[j:])
   # Trim to top 5 elements
   return sorted(result, reverse=True)
def merge_sort(arr):
   # Base case: single element is already sorted
   if len(arr) <= 1:
       return arr
   mid = len(arr) // 2
   left = merge_sort(arr[:mid])
   right = merge_sort(arr[mid:])
   return merge(left, right)
# Example usage
data = [12, 45, 23, 89, 34, 67, 78, 90, 11]
sorted_top_5 = merge_sort(data)
print("Top 5 highest records:", sorted_top_5)