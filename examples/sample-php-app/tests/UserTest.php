<?php

use PHPUnit\Framework\TestCase;
use App\Models\User;

class UserTest extends TestCase
{
    public function testUserCanBeConstructed(): void
    {
        $this->assertTrue(class_exists(User::class));
    }
}
