# 用户功能实现分析

## 1. 后端用户相关实现

### 1.1 注册接口

**代码片段**：
```python
@api_view(['POST'])
@permission_classes([AllowAny]) 
def register(request):
    """处理 Vue 前端的注册请求"""
    username = request.data.get('username')
    password = request.data.get('password')
    email = request.data.get('email', '') 

    if not username or not password:
        return Response({'error': '用户名和密码不能为空'}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username=username).exists():
        return Response({'error': '该用户名已被注册'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.create_user(username=username, password=password, email=email)
        visitor_group = Group.objects.get(name='游客')
        user.groups.add(visitor_group)
        return Response({
            'message': '注册成功',
            'user_id': user.id
        }, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
```

**作用**：
- 处理前端注册请求，验证用户名和密码是否为空
- 检查用户名是否已被注册
- 创建新用户并将其添加到"游客"用户组
- 返回注册成功信息或错误信息

### 1.2 登录接口

**代码片段**：
```python
# 在 urls.py 中配置
path('api/login/', TokenObtainPairView.as_view(), name='login'),
```

**作用**：
- 使用Django REST Framework Simple JWT提供的TokenObtainPairView处理登录请求
- 验证用户凭据并返回JWT访问令牌

### 1.3 获取用户信息接口

**代码片段**：
```python
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_info(request):
    """获取当前登录用户的信息"""
    user = request.user
    group_name = user.groups.first().name if user.groups.exists() else "无分组"
    
    return Response({
        'username': user.username,
        'email': user.email,
        'real_name': user.first_name, 
        'group': group_name
    })
```

**作用**：
- 获取当前登录用户的详细信息，包括用户名、邮箱、真实姓名和用户组
- 只允许已认证用户访问

### 1.4 更新用户资料接口

**代码片段**：
```python
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    """处理前端修改资料（账号、姓名、邮箱）的请求"""
    user = request.user
    data = request.data
    
    new_username = data.get('username', '').strip()
    new_email = data.get('email', '').strip()
    new_real_name = data.get('real_name', '').strip()

    if new_username and new_username != user.username:
        if User.objects.filter(username=new_username).exists():
            return Response({"error": "该用户名已被占用，请换一个"}, status=status.HTTP_400_BAD_REQUEST)
        user.username = new_username

    if 'email' in data:
        user.email = new_email
    if 'real_name' in data:
        user.first_name = new_real_name
        
    user.save()
    
    return Response({
        'status': 'success',
        'message': '个人资料更新成功！',
        'new_username': user.username
    })
```

**作用**：
- 处理用户资料更新请求，包括用户名、邮箱和真实姓名
- 验证用户名是否已被占用
- 保存更新后的用户信息并返回成功信息

### 1.5 修改密码接口

**代码片段**：
```python
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """处理修改密码逻辑"""
    user = request.user
    new_pwd = request.data.get('new_password')
    
    if not new_pwd:
        return Response({'error': '密码不能为空'}, status=status.HTTP_400_BAD_REQUEST)
    
    user.set_password(new_pwd)
    user.save()
    
    return Response({'message': '修改成功'})
```

**作用**：
- 处理用户密码修改请求
- 验证新密码是否为空
- 使用Django的set_password方法安全地更新密码

## 2. 前端用户相关实现

### 2.1 登录组件

**代码片段**：
```vue
const handleLogin = async () => {
  // 基础检查：别空着手去
  if (!loginForm.username || !loginForm.password) {
    ElMessage.warning('请填写用户名和密码')
    return
  }

  try {
    // 2. 发送 POST 请求到 Django 的登录接口
    // 注意：这里的端口 8000 是你 Django 运行的地址
    const response = await axios.post('http://127.0.0.1:8000/api/login/', {
      username: loginForm.username,
      password: loginForm.password
    })

    // 3. 如果成功，Django 会返回一串 Token（通行证）
    const token = response.data.access
    localStorage.setItem('token', response.data.access)// 把通行证存在浏览器里，下次不用再登录
    localStorage.setItem('username', loginForm.username)

    ElMessage.success('登录成功！欢迎进入巡课系统')
    router.push('/dashboard')
    
    // 4. 这里暂时打印一下，证明我们拿到通行证了
    console.log('拿到的通行证是：', token)

  } catch (error) {
    // 5. 如果失败（密码错了、用户名不存在、或者 Django 没开）
    console.error(error)
    ElMessage.error('登录失败：用户名或密码错误，或后端未启动')
  }
}
```

**作用**：
- 处理用户登录逻辑，验证输入字段
- 发送登录请求到后端API
- 存储JWT令牌到localStorage
- 登录成功后跳转到仪表盘页面
- 处理登录失败的异常情况

### 2.2 注册组件

**代码片段**：
```vue
const doRegister = async () => {
  try {
    const res = await axios.post('http://127.0.0.1:8000/api/register/', {
      username: username.value,
      password: password.value,
      email: email.value
    })
    
    ElMessage.success('注册成功！请登录')
    router.push('/login') // 注册完自动跳回登录页面
  } catch (err) {
    ElMessage.error('注册失败，用户名可能重复了')
  }
}
```

**作用**：
- 处理用户注册逻辑，发送注册请求到后端API
- 注册成功后跳转到登录页面
- 处理注册失败的异常情况

### 2.3 个人资料组件

**代码片段**：
```vue
// 1. 获取个人信息
const fetchUserInfo = async () => {
  try {
    const token = localStorage.getItem('token')
    if (!token) return router.push('/login')
    const res = await axios.get('http://localhost:8000/api/user-info/', {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    userInfo.username = res.data.username
    userInfo.email = res.data.email
    userInfo.real_name = res.data.real_name || ''
    userGroup.value = res.data.group
  } catch (err) {
    ElMessage.error('身份验证失效或获取信息失败')
    if(err.response?.status === 401) router.push('/login')
  }
}

// 2. 保存资料修改 (包含姓名和邮箱)
const saveProfile = async () => {
  if (!userInfo.real_name.trim()) {
    ElMessage.warning('真实姓名不能为空！')
    return
  }

  saving.value = true
  try {
    const token = localStorage.getItem('token')
    await axios.post('http://localhost:8000/api/update-profile/', 
      { 
        email: userInfo.email,
        real_name: userInfo.real_name 
      }, 
      { headers: { 'Authorization': `Bearer ${token}` } }
    )
    ElMessage.success('个人资料更新成功')
    
    
  } catch (err) { 
    ElMessage.error(err.response?.data?.error || '资料更新失败') 
  } finally { 
    saving.value = false 
  }
}

const handlePasswordChange = async () => {
  if (!passwordForm.newPassword) {
    ElMessage.warning('新密码不能为空')
    return
  }
  if (passwordForm.newPassword !== passwordForm.confirmPassword) {
    ElMessage.warning('两次输入的密码不一致！')
    return
  }
  try {
    const token = localStorage.getItem('token')
    await axios.post('http://localhost:8000/api/change-password/', {
      new_password: passwordForm.newPassword
    }, { headers: { 'Authorization': `Bearer ${token}` } })
    
    ElMessageBox.alert('密码修改成功，请使用新密码重新登录系统', '安全提示', {
      confirmButtonText: '去登录',
      type: 'success',
      callback: () => { 
        localStorage.clear()
        router.push('/login')
      }
    })
  } catch (err) { 
    ElMessage.error('修改密码失败，请检查网络或联系管理员') 
  }
}
```

**作用**：
- 获取当前用户信息并显示在界面上
- 处理用户资料更新请求
- 处理用户密码修改请求，包括密码验证和确认
- 密码修改成功后提示用户重新登录

### 2.4 路由守卫

**代码片段**：
```javascript
// 💡 导航守卫：防止未登录用户直接访问 dashboard
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('access') || localStorage.getItem('token')
  
  if (to.path.startsWith('/dashboard') && !token) {
    // 如果去后台页面但没 token，强制踢回登录页
    next('/login')
  } else {
    next()
  }
})
```

**作用**：
- 确保只有登录用户才能访问后台页面
- 未登录用户访问后台页面时会被重定向到登录页面

## 3. 用户功能交互流程

### 3.1 注册流程
1. 用户访问注册页面，输入用户名、密码和邮箱
2. 前端验证输入字段，发送注册请求到后端
3. 后端验证用户名是否已存在，创建新用户并添加到"游客"组
4. 前端收到注册成功响应，跳转到登录页面

### 3.2 登录流程
1. 用户访问登录页面，输入用户名和密码
2. 前端验证输入字段，发送登录请求到后端
3. 后端验证用户凭据，返回JWT访问令牌
4. 前端存储令牌到localStorage，跳转到仪表盘页面

### 3.3 个人资料管理流程
1. 用户访问个人资料页面
2. 前端发送请求获取用户信息并显示
3. 用户修改个人资料或密码
4. 前端验证输入字段，发送更新请求到后端
5. 后端更新用户信息，返回成功响应
6. 前端显示成功提示

### 3.4 异常处理
1. 注册时用户名已存在：返回错误信息
2. 登录时用户名或密码错误：返回错误信息
3. 未登录用户访问后台页面：重定向到登录页面
4. 令牌过期或无效：返回401错误，前端跳转到登录页面
5. 网络错误：显示错误提示

## 4. 技术实现要点

1. **认证机制**：使用JWT（JSON Web Token）进行用户认证，实现无状态会话管理
2. **权限控制**：使用Django REST Framework的permission_classes装饰器控制接口访问权限
3. **前端状态管理**：使用localStorage存储用户令牌和基本信息
4. **路由保护**：使用Vue Router的导航守卫确保只有登录用户才能访问后台页面
5. **错误处理**：前后端都实现了完善的错误处理机制，确保用户体验
6. **数据验证**：前后端都对用户输入进行验证，确保数据完整性

## 5. 代码优化建议

1. **前端API地址配置**：将API地址提取为配置项，避免硬编码
2. **密码强度验证**：增加密码强度验证，提高安全性
3. **令牌刷新机制**：实现JWT令牌自动刷新，避免用户频繁登录
4. **表单验证增强**：使用Element Plus的表单验证规则，提供更详细的错误提示
5. **后端错误处理**：统一错误处理机制，返回更标准化的错误信息
6. **前端状态管理**：使用Pinia或Vuex管理全局状态，提高代码可维护性

## 6. 总结

本系统的用户功能实现采用了前后端分离架构，后端使用Django和Django REST Framework提供RESTful API，前端使用Vue 3和Element Plus构建用户界面。通过JWT认证机制实现了安全的用户认证，通过路由守卫和权限控制确保了系统的安全性。用户功能包括注册、登录、个人资料管理和密码修改，涵盖了基本的用户管理需求。

系统的实现遵循了现代Web应用开发的最佳实践，代码结构清晰，功能完善，用户体验良好。同时，也存在一些可优化的空间，如API地址配置、密码强度验证、令牌刷新机制等，这些优化可以进一步提高系统的安全性和用户体验。