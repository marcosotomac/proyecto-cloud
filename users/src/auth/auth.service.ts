import {
  Injectable,
  UnauthorizedException,
  BadRequestException,
} from '@nestjs/common';
import { JwtService } from '@nestjs/jwt';
import { ConfigService } from '@nestjs/config';
import { UsersService } from '../users/users.service';
import {
  JwtPayload,
  AuthResponse,
  TokenPair,
} from './interfaces/auth.interface';
import { RegisterDto, LoginDto, RefreshTokenDto } from './dto/auth.dto';
import * as bcrypt from 'bcryptjs';

@Injectable()
export class AuthService {
  constructor(
    private usersService: UsersService,
    private jwtService: JwtService,
    private configService: ConfigService,
  ) {}

  async register(
    registerDto: RegisterDto,
    userAgent?: string,
    ip?: string,
  ): Promise<AuthResponse> {
    const { email, password } = registerDto;

    // Crear el usuario
    const user = await this.usersService.createUser(email, password);

    // Generar tokens
    const tokens = await this.generateTokens({
      sub: user.id,
      email: user.email,
      role: user.role,
    });

    // Crear sesión
    const refreshTokenHash = await bcrypt.hash(tokens.refreshToken, 10);
    await this.usersService.createSession(
      user.id,
      refreshTokenHash,
      userAgent,
      ip,
    );

    return {
      user: {
        id: user.id,
        email: user.email,
        role: user.role,
        createdAt: user.createdAt,
      },
      accessToken: tokens.accessToken,
      refreshToken: tokens.refreshToken,
    };
  }

  async login(
    loginDto: LoginDto,
    userAgent?: string,
    ip?: string,
  ): Promise<AuthResponse> {
    const { email, password } = loginDto;

    // Buscar el usuario
    const user = await this.usersService.findUserByEmail(email);
    if (!user) {
      throw new UnauthorizedException('Invalid credentials');
    }

    // Validar contraseña
    const isPasswordValid = await this.usersService.validatePassword(
      user,
      password,
    );
    if (!isPasswordValid) {
      throw new UnauthorizedException('Invalid credentials');
    }

    // Generar tokens
    const tokens = await this.generateTokens({
      sub: user.id,
      email: user.email,
      role: user.role,
    });

    // Crear sesión
    const refreshTokenHash = await bcrypt.hash(tokens.refreshToken, 10);
    await this.usersService.createSession(
      user.id,
      refreshTokenHash,
      userAgent,
      ip,
    );

    return {
      user: {
        id: user.id,
        email: user.email,
        role: user.role,
        createdAt: user.createdAt,
      },
      accessToken: tokens.accessToken,
      refreshToken: tokens.refreshToken,
    };
  }

  async refresh(refreshTokenDto: RefreshTokenDto): Promise<TokenPair> {
    const { refreshToken } = refreshTokenDto;

    try {
      // Verificar el refresh token
      const payload = this.jwtService.verify(refreshToken, {
        secret: this.configService.get('JWT_REFRESH_SECRET'),
      });

      // Buscar la sesión
      const refreshTokenHash = await bcrypt.hash(refreshToken, 10);
      const session =
        await this.usersService.findSessionByRefreshToken(refreshTokenHash);

      if (!session) {
        throw new UnauthorizedException('Invalid refresh token');
      }

      // Generar nuevos tokens
      const tokens = await this.generateTokens({
        sub: session.user.id,
        email: session.user.email,
        role: session.user.role,
      });

      // Revocar la sesión anterior y crear una nueva
      await this.usersService.revokeSession(session.id);
      const newRefreshTokenHash = await bcrypt.hash(tokens.refreshToken, 10);
      await this.usersService.createSession(
        session.userId,
        newRefreshTokenHash,
      );

      return tokens;
    } catch (error) {
      throw new UnauthorizedException('Invalid refresh token');
    }
  }

  async logout(refreshToken: string): Promise<void> {
    try {
      const refreshTokenHash = await bcrypt.hash(refreshToken, 10);
      const session =
        await this.usersService.findSessionByRefreshToken(refreshTokenHash);

      if (session) {
        await this.usersService.revokeSession(session.id);
      }
    } catch (error) {
      // Silently fail - logout should always succeed
    }
  }

  async validateJwtPayload(payload: JwtPayload) {
    const user = await this.usersService.findUserById(payload.sub);
    if (!user) {
      throw new UnauthorizedException('User not found');
    }
    return user;
  }

  private async generateTokens(payload: JwtPayload): Promise<TokenPair> {
    const [accessToken, refreshToken] = await Promise.all([
      this.jwtService.signAsync(payload, {
        secret: this.configService.get('JWT_ACCESS_SECRET'),
        expiresIn: this.configService.get('JWT_ACCESS_EXPIRATION', '15m'),
      }),
      this.jwtService.signAsync(payload, {
        secret: this.configService.get('JWT_REFRESH_SECRET'),
        expiresIn: this.configService.get('JWT_REFRESH_EXPIRATION', '30d'),
      }),
    ]);

    return { accessToken, refreshToken };
  }
}
