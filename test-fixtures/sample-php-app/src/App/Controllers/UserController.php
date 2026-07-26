<?php

namespace App\Controllers;

use App\Models\User;
use Illuminate\Http\Request;

class UserController
{
    public function show(Request $request, int $id): User
    {
        return User::findOrFail($id);
    }
}
